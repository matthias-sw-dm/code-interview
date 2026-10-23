// Mock backend for the frontend exercise. No dependencies, everything in memory,
// data resets on restart. Latency and random write failures are on by default:
//
//   node mock-api/server.mjs                  # default, ~150-500ms latency, 15% failing writes
//   LATENCY=0 FAIL_RATE=0 node mock-api/...   # calm mode while you debug
//
import { createServer } from 'node:http'

const PORT = Number(process.env.PORT ?? 4000)
const LATENCY = Number(process.env.LATENCY ?? 1)
const FAIL_RATE = Number(process.env.FAIL_RATE ?? 0.15)

const PASSWORD = 'demo'
const DEFAULT_PAGE_SIZE = 25
const MAX_PAGE_SIZE = 100
const PRIORITIES = ['low', 'medium', 'high']
const SORT_FIELDS = ['due', 'priority', 'title', 'created']
const TAGS = ['home', 'work', 'urgent', 'errand', 'later']
const MAX_LOGIN_ATTEMPTS = 5
const LOCKOUT_MS = 60_000

const bootedAt = new Date()

const dayIso = (offset) => {
  const d = new Date(bootedAt)
  d.setDate(d.getDate() + offset)
  return d.toISOString().slice(0, 10)
}

// Lehmer RNG so the seed data is identical on every restart.
let rngState = 42
const rnd = () => {
  rngState = (rngState * 48271) % 2147483647
  return rngState / 2147483647
}
const pick = (xs) => xs[Math.floor(rnd() * xs.length)]

const users = [
  { id: 'u1', email: 'ada@example.com', name: 'Ada Lovelace' },
  { id: 'u2', email: 'grace@example.com', name: 'Grace Hopper' },
]

const lists = []
const items = []
let itemSeq = 0
let listSeq = 0

const addList = (name, ownerId, shares = []) => {
  listSeq += 1
  const list = { id: `l${listSeq}`, name, ownerId, shares, createdAt: bootedAt.toISOString() }
  lists.push(list)
  return list
}

const addItem = (listId, title, ownerId, overrides = {}) => {
  itemSeq += 1
  const item = {
    id: `i${itemSeq}`,
    listId,
    title,
    description: null,
    dueDate: rnd() < 0.15 ? null : dayIso(Math.floor(rnd() * 28) - 7),
    priority: pick(PRIORITIES),
    done: rnd() < 0.3,
    tags: rnd() < 0.6 ? [pick(TAGS)] : [],
    version: 1,
    deletedAt: null,
    createdAt: bootedAt.toISOString(),
    createdBy: ownerId,
    updatedAt: bootedAt.toISOString(),
    updatedBy: ownerId,
    ...overrides,
  }
  items.push(item)
  return item
}

const seed = (list, count, pool) => {
  for (let i = 0; i < count; i += 1) {
    const round = Math.floor(i / pool.length)
    const title = round === 0 ? pool[i] : `${pool[i % pool.length]} (${round + 1})`
    addItem(list.id, title, list.ownerId)
  }
}

seed(addList('Groceries', 'u1'), 12, ['Oat milk', 'Tomatoes', 'Coffee beans', 'Sourdough', 'Olive oil', 'Eggs'])
seed(addList('Work', 'u1'), 40, [
  'Review PR #412',
  'Write ADR for caching',
  'Prepare sprint demo',
  'Fix flaky checkout test',
  'Update onboarding docs',
  'Answer customer ticket',
])
seed(addList('Someday', 'u1'), 5, ['Learn Rust', 'Repaint the hallway', 'Plan cycling trip'])
const backlog = addList('Backlog', 'u1')
for (let i = 0; i < 500; i += 1) addItem(backlog.id, `Backlog item ${i + 1}`, 'u1')
seed(addList('Team Retro', 'u2', [{ userId: 'u1', role: 'write' }]), 15, [
  'Too many meetings',
  'Deploys are slow',
  'Pairing worked well',
  'Alerting is noisy',
])
seed(addList('Household', 'u2', [{ userId: 'u1', role: 'read' }]), 8, [
  'Descale the kettle',
  'Water the plants',
  'Take out recycling',
])

const sessions = new Map() // token -> userId
const loginAttempts = new Map() // email -> { count, lockedUntil }

const roleFor = (user, list) =>
  list.ownerId === user.id ? 'owner' : (list.shares.find((s) => s.userId === user.id)?.role ?? null)

const canWrite = (user, list) => ['owner', 'write'].includes(roleFor(user, list))

const visibleLists = (user) => lists.filter((list) => roleFor(user, list) !== null)

const liveItems = (listId) => items.filter((i) => i.listId === listId && !i.deletedAt)

const listDto = (user, list) => ({
  id: list.id,
  name: list.name,
  role: roleFor(user, list),
  owner: users.find((u) => u.id === list.ownerId).name,
  itemCount: liveItems(list.id).length,
  openCount: liveItems(list.id).filter((i) => !i.done).length,
})

const itemDto = (item) => ({
  id: item.id,
  listId: item.listId,
  title: item.title,
  description: item.description,
  dueDate: item.dueDate,
  priority: item.priority,
  done: item.done,
  tags: item.tags,
  version: item.version,
  updatedAt: item.updatedAt,
  updatedBy: users.find((u) => u.id === item.updatedBy)?.name ?? null,
})

const send = (res, status, body) => {
  res.writeHead(status, {
    'content-type': 'application/json',
    'access-control-allow-origin': '*',
    'access-control-allow-headers': 'authorization, content-type',
    'access-control-allow-methods': 'GET, POST, PATCH, DELETE, OPTIONS',
  })
  res.end(body === undefined ? '' : JSON.stringify(body))
}

const fail = (res, status, code, message, extra) =>
  send(res, status, { error: { code, message, ...extra } })

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const readBody = async (req) => {
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  if (chunks.length === 0) return {}
  return JSON.parse(Buffer.concat(chunks).toString())
}

const validateItem = (body, { partial }) => {
  const fields = {}
  const has = (key) => Object.hasOwn(body, key)

  if (!partial || has('title')) {
    const title = body.title
    if (typeof title !== 'string' || title.trim() === '') fields.title = 'must not be empty'
    else if (title.length > 120) fields.title = 'must be at most 120 characters'
  }
  if (has('description') && body.description !== null) {
    if (typeof body.description !== 'string') fields.description = 'must be a string or null'
    else if (body.description.length > 2000) fields.description = 'must be at most 2000 characters'
  }
  if (has('dueDate') && body.dueDate !== null && !/^\d{4}-\d{2}-\d{2}$/.test(body.dueDate ?? '')) {
    fields.dueDate = 'must be an ISO date (YYYY-MM-DD) or null'
  }
  if (has('priority') && !PRIORITIES.includes(body.priority)) {
    fields.priority = `must be one of ${PRIORITIES.join(', ')}`
  }
  if (has('done') && typeof body.done !== 'boolean') fields.done = 'must be a boolean'
  if (has('tags') && (!Array.isArray(body.tags) || body.tags.some((t) => typeof t !== 'string'))) {
    fields.tags = 'must be an array of strings'
  }

  return Object.keys(fields).length > 0 ? fields : null
}

const touch = (item, user, changes) => {
  Object.assign(item, changes)
  item.version += 1
  item.updatedAt = new Date().toISOString()
  item.updatedBy = user.id
  return item
}

const login = async ({ res, body }) => {
  const email = String(body.email ?? '').toLowerCase()
  const attempt = loginAttempts.get(email) ?? { count: 0, lockedUntil: 0 }

  if (attempt.lockedUntil > Date.now()) {
    return fail(res, 429, 'too_many_attempts', 'Too many failed logins, try again later', {
      retryAfter: Math.ceil((attempt.lockedUntil - Date.now()) / 1000),
    })
  }

  const user = users.find((u) => u.email === email)
  if (!user || body.password !== PASSWORD) {
    attempt.count += 1
    if (attempt.count >= MAX_LOGIN_ATTEMPTS) {
      attempt.count = 0
      attempt.lockedUntil = Date.now() + LOCKOUT_MS
    }
    loginAttempts.set(email, attempt)
    return fail(res, 401, 'invalid_credentials', 'Unknown email or wrong password')
  }

  loginAttempts.delete(email)
  const token = `token-${user.id}-${sessions.size + 1}`
  sessions.set(token, user.id)
  return send(res, 200, { token, user: { id: user.id, email: user.email, name: user.name } })
}

const routes = [
  ['POST', /^\/api\/auth\/login$/, login, { public: true }],

  ['GET', /^\/api\/auth\/me$/, ({ res, user }) => send(res, 200, user)],

  ['GET', /^\/api\/lists$/, ({ res, user }) =>
    send(res, 200, visibleLists(user).map((list) => listDto(user, list)))],

  ['POST', /^\/api\/lists$/, ({ res, user, body }) => {
    if (typeof body.name !== 'string' || body.name.trim() === '') {
      return fail(res, 422, 'validation_failed', 'Invalid list', { fields: { name: 'must not be empty' } })
    }
    const list = addList(body.name.trim(), user.id)
    return send(res, 201, listDto(user, list))
  }],

  ['PATCH', /^\/api\/lists\/([^/]+)$/, ({ res, user, body, params }) => {
    const list = lists.find((l) => l.id === params[0])
    if (!list || roleFor(user, list) === null) return fail(res, 404, 'not_found', 'No such list')
    if (roleFor(user, list) !== 'owner') return fail(res, 403, 'forbidden', 'Only the owner can rename a list')
    if (typeof body.name !== 'string' || body.name.trim() === '') {
      return fail(res, 422, 'validation_failed', 'Invalid list', { fields: { name: 'must not be empty' } })
    }
    list.name = body.name.trim()
    return send(res, 200, listDto(user, list))
  }],

  ['DELETE', /^\/api\/lists\/([^/]+)$/, ({ res, user, params }) => {
    const list = lists.find((l) => l.id === params[0])
    if (!list || roleFor(user, list) === null) return fail(res, 404, 'not_found', 'No such list')
    if (roleFor(user, list) !== 'owner') return fail(res, 403, 'forbidden', 'Only the owner can delete a list')
    lists.splice(lists.indexOf(list), 1)
    for (const item of liveItems(list.id)) item.deletedAt = new Date().toISOString()
    return send(res, 204)
  }],

  ['GET', /^\/api\/lists\/([^/]+)\/items$/, ({ res, user, url, params }) => {
    const list = lists.find((l) => l.id === params[0])
    if (!list || roleFor(user, list) === null) return fail(res, 404, 'not_found', 'No such list')

    const q = url.searchParams
    let result = liveItems(list.id)

    if (q.has('done')) result = result.filter((i) => i.done === (q.get('done') === 'true'))
    if (q.get('q')) {
      const needle = q.get('q').toLowerCase()
      result = result.filter((i) => i.title.toLowerCase().includes(needle))
    }
    const tags = q.getAll('tag').filter(Boolean)
    if (tags.length > 0) result = result.filter((i) => tags.every((t) => i.tags.includes(t)))
    if (q.get('dueFrom')) result = result.filter((i) => i.dueDate && i.dueDate >= q.get('dueFrom'))
    if (q.get('dueTo')) result = result.filter((i) => i.dueDate && i.dueDate <= q.get('dueTo'))

    const sortParam = q.get('sort') ?? 'due'
    const desc = sortParam.startsWith('-')
    const field = desc ? sortParam.slice(1) : sortParam
    if (!SORT_FIELDS.includes(field)) {
      return fail(res, 422, 'validation_failed', 'Invalid query', {
        fields: { sort: `must be one of ${SORT_FIELDS.join(', ')}, optionally prefixed with -` },
      })
    }
    const key = {
      due: (i) => i.dueDate ?? '9999-12-31',
      priority: (i) => PRIORITIES.indexOf(i.priority),
      title: (i) => i.title.toLowerCase(),
      created: (i) => i.createdAt + i.id,
    }[field]
    result = [...result].sort((a, b) => (key(a) < key(b) ? -1 : key(a) > key(b) ? 1 : 0))
    if (desc) result.reverse()

    const page = Math.max(1, Number(q.get('page') ?? 1))
    const pageSize = Math.min(MAX_PAGE_SIZE, Math.max(1, Number(q.get('pageSize') ?? DEFAULT_PAGE_SIZE)))
    const start = (page - 1) * pageSize

    return send(res, 200, {
      items: result.slice(start, start + pageSize).map(itemDto),
      page,
      pageSize,
      total: result.length,
    })
  }],

  ['POST', /^\/api\/lists\/([^/]+)\/items$/, ({ res, user, body, params }) => {
    const list = lists.find((l) => l.id === params[0])
    if (!list || roleFor(user, list) === null) return fail(res, 404, 'not_found', 'No such list')
    if (!canWrite(user, list)) return fail(res, 403, 'forbidden', 'No write access to this list')

    const fields = validateItem(body, { partial: false })
    if (fields) return fail(res, 422, 'validation_failed', 'Invalid item', { fields })

    const item = addItem(list.id, body.title.trim(), user.id, {
      description: body.description ?? null,
      dueDate: body.dueDate ?? null,
      priority: body.priority ?? 'medium',
      done: body.done ?? false,
      tags: body.tags ?? [],
    })
    return send(res, 201, itemDto(item))
  }],

  ['GET', /^\/api\/items\/([^/]+)$/, ({ res, user, params }) => {
    const item = items.find((i) => i.id === params[0] && !i.deletedAt)
    const list = item && lists.find((l) => l.id === item.listId)
    if (!item || !list || roleFor(user, list) === null) return fail(res, 404, 'not_found', 'No such item')
    return send(res, 200, itemDto(item))
  }],

  ['PATCH', /^\/api\/items\/([^/]+)$/, ({ res, user, body, params }) => {
    const item = items.find((i) => i.id === params[0] && !i.deletedAt)
    const list = item && lists.find((l) => l.id === item.listId)
    if (!item || !list || roleFor(user, list) === null) return fail(res, 404, 'not_found', 'No such item')
    if (!canWrite(user, list)) return fail(res, 403, 'forbidden', 'No write access to this list')

    if (typeof body.version !== 'number') {
      return fail(res, 422, 'validation_failed', 'Invalid item', { fields: { version: 'is required' } })
    }
    if (body.version !== item.version) {
      return fail(res, 409, 'conflict', 'The item changed since you loaded it', { current: itemDto(item) })
    }

    const fields = validateItem(body, { partial: true })
    if (fields) return fail(res, 422, 'validation_failed', 'Invalid item', { fields })

    const changes = {}
    for (const key of ['title', 'description', 'dueDate', 'priority', 'done', 'tags']) {
      if (Object.hasOwn(body, key)) changes[key] = key === 'title' ? body.title.trim() : body[key]
    }
    return send(res, 200, itemDto(touch(item, user, changes)))
  }],

  ['DELETE', /^\/api\/items\/([^/]+)$/, ({ res, user, params }) => {
    const item = items.find((i) => i.id === params[0] && !i.deletedAt)
    const list = item && lists.find((l) => l.id === item.listId)
    if (!item || !list || roleFor(user, list) === null) return fail(res, 404, 'not_found', 'No such item')
    if (!canWrite(user, list)) return fail(res, 403, 'forbidden', 'No write access to this list')
    item.deletedAt = new Date().toISOString()
    return send(res, 204)
  }],

  ['POST', /^\/api\/items\/([^/]+)\/restore$/, ({ res, user, params }) => {
    const item = items.find((i) => i.id === params[0] && i.deletedAt)
    const list = item && lists.find((l) => l.id === item.listId)
    if (!item || !list || roleFor(user, list) === null) return fail(res, 404, 'not_found', 'No such item')
    if (!canWrite(user, list)) return fail(res, 403, 'forbidden', 'No write access to this list')
    item.deletedAt = null
    return send(res, 200, itemDto(item))
  }],

  ['POST', /^\/api\/items\/([^/]+)\/move$/, ({ res, user, body, params }) => {
    const item = items.find((i) => i.id === params[0] && !i.deletedAt)
    const source = item && lists.find((l) => l.id === item.listId)
    const target = lists.find((l) => l.id === body.listId)
    if (!item || !source || roleFor(user, source) === null) return fail(res, 404, 'not_found', 'No such item')
    if (!target || roleFor(user, target) === null) return fail(res, 404, 'not_found', 'No such target list')
    if (!canWrite(user, source) || !canWrite(user, target)) {
      return fail(res, 403, 'forbidden', 'No write access to source or target list')
    }
    return send(res, 200, itemDto(touch(item, user, { listId: target.id })))
  }],

  ['POST', /^\/api\/items\/bulk$/, ({ res, user, body }) => {
    if (!Array.isArray(body.ids) || typeof body.done !== 'boolean') {
      return fail(res, 422, 'validation_failed', 'Invalid bulk update', {
        fields: { ids: 'must be an array of item ids', done: 'must be a boolean' },
      })
    }

    const updated = []
    const failed = []
    for (const id of body.ids) {
      const item = items.find((i) => i.id === id && !i.deletedAt)
      const list = item && lists.find((l) => l.id === item.listId)
      if (!item || !list || roleFor(user, list) === null) failed.push({ id, code: 'not_found' })
      else if (!canWrite(user, list)) failed.push({ id, code: 'forbidden' })
      else updated.push(itemDto(touch(item, user, { done: body.done })))
    }
    return send(res, 200, { updated, failed })
  }],

  ['GET', /^\/api\/tags$/, ({ res, user }) => {
    const counts = new Map()
    for (const list of visibleLists(user)) {
      for (const item of liveItems(list.id)) {
        for (const tag of item.tags) counts.set(tag, (counts.get(tag) ?? 0) + 1)
      }
    }
    return send(res, 200, [...counts]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => a.name.localeCompare(b.name)))
  }],
]

const server = createServer(async (req, res) => {
  if (req.method === 'OPTIONS') return send(res, 204)

  const url = new URL(req.url, `http://localhost:${PORT}`)
  const match = routes.find(([method, pattern]) => method === req.method && pattern.test(url.pathname))

  if (!match) {
    const wrongMethod = routes.some(([, pattern]) => pattern.test(url.pathname))
    return wrongMethod
      ? fail(res, 405, 'method_not_allowed', `${req.method} is not allowed on ${url.pathname}`)
      : fail(res, 404, 'not_found', `${url.pathname} does not exist`)
  }

  const [, pattern, handler, options = {}] = match
  const params = url.pathname.match(pattern).slice(1)

  if (LATENCY > 0) await sleep(LATENCY * (150 + Math.random() * 350))

  let body = {}
  if (req.method !== 'GET') {
    try {
      body = await readBody(req)
    } catch {
      return fail(res, 400, 'invalid_json', 'Request body is not valid JSON')
    }
  }

  let user = null
  if (!options.public) {
    const token = (req.headers.authorization ?? '').replace(/^Bearer /, '')
    const userId = sessions.get(token)
    if (!userId) return fail(res, 401, 'unauthenticated', 'Missing or unknown token')
    const { id, email, name } = users.find((u) => u.id === userId)
    user = { id, email, name }
  }

  // Writes fail sometimes, on purpose. Login is spared so you never get locked out.
  if (req.method !== 'GET' && !options.public && Math.random() < FAIL_RATE) {
    return fail(res, 500, 'internal_error', 'The server dropped this one')
  }

  try {
    await handler({ req, res, url, body, params, user })
  } catch (error) {
    console.error(error)
    fail(res, 500, 'internal_error', 'Unhandled error')
  }
})

server.listen(PORT, () => {
  console.log(`mock api on http://localhost:${PORT}  (latency x${LATENCY}, fail rate ${FAIL_RATE})`)
  console.log(`login with ${users.map((u) => u.email).join(' / ')} and password "${PASSWORD}"`)
})
