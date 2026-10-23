# MR Review Exercise — Interviewer Notes

The pipeline in `.gitlab-ci.yml` + `ci.yml` contains four intentional bugs.
Candidates should identify them during the MR review exercise.

______________________________________________________________________

## Bug 1 — Wrong rules extension on `deploy_feature`

**File:** `ci.yml`, job `deploy_feature`

**Code:**

```yaml
deploy_feature:
  extends:
    - .docker_vars
    - .rules_mr    # intended to restrict to MR pipelines
    - .rules_main  # accidentally overrides the above
```

**Problem:** GitLab resolves `extends` by deep-merging keys top-to-bottom; for `rules:`, which is a list, the last fragment wins entirely — there is no list merge. As a result `deploy_feature` inherits `.rules_main`'s rule and only runs on the default branch, never on MRs.

**Fix:** Remove `.rules_main` from the extends list and keep only `.rules_mr`.

______________________________________________________________________

## Bug 2 — Missing `artifacts:` on `build`

**File:** `ci.yml`, job `build`

**Code:**

```yaml
build:
  script:
    - docker build -t $IMAGE .
    - docker push $IMAGE
    - echo $IMAGE > image.txt   # written but never declared as artifact
```

**Problem:** `deploy_feature`, `deploy_staging`, and `deploy_prod` all read `image.txt` via `cat image.txt`. Without an `artifacts:` block the file is discarded at job end and downstream jobs receive an empty workspace, causing silent failures.

**Fix:**

```yaml
artifacts:
  paths:
    - image.txt
  expire_in: 1 day
```

______________________________________________________________________

## Bug 3 — `stop_feature` missing `when: manual` and `allow_failure: true`

**File:** `ci.yml`, job `stop_feature`

**Code:**

```yaml
stop_feature:
  environment:
    name: feature-$CI_MERGE_REQUEST_IID
    action: stop
  rules:
    - if: $CI_MERGE_REQUEST_IID   # missing when: manual + allow_failure: true
```

**Problem:** GitLab requires that the rule triggering an environment stop job includes `when: manual` and `allow_failure: true`. Without them GitLab cannot link the stop action to the environment correctly and will surface a validation error.

**Fix:**

```yaml
rules:
  - if: $CI_MERGE_REQUEST_IID
    when: manual
    allow_failure: true
```

______________________________________________________________________

## Bug 4 — `deploy_prod` runs automatically after staging

**File:** `.gitlab-ci.yml`, job `deploy_prod`

**Code:**

```yaml
deploy_prod:
  needs:
    - job: deploy_staging
  # no when: manual — fires automatically on every main branch push
  script:
    - kubectl set image deployment/app app=$IMAGE --namespace=prod
```

**Problem:** Every push to the default branch that passes staging will immediately deploy to production without any human gate. This is a dangerous default for a production environment.

**Fix:** Add `when: manual` (either in a `rules:` block or directly on the job) so the deploy requires an explicit trigger.
