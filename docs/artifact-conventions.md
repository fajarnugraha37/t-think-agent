# Artifact conventions

Every v2.3 work item stores state, lane assessment, phase waivers, delegations, result envelopes, boundary reports, evidence, canonical aggregate artifacts, and composite component artifacts below `.t-think/<work-id>/`. Composite component artifacts use `artifacts/components/<phase>/<track>.yaml`; only the aggregate phase artifact may advance lifecycle state. Runtime files may be ignored locally only when durable artifacts and approvals remain available for continuation.
