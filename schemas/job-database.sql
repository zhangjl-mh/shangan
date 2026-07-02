PRAGMA foreign_keys = ON;
PRAGMA user_version = 500;

CREATE TABLE build_meta (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  schema_version TEXT NOT NULL CHECK (schema_version = '5.0'),
  build_id TEXT NOT NULL UNIQUE,
  generated_at TEXT NOT NULL,
  as_of TEXT NOT NULL,
  profile_sha256 TEXT NOT NULL CHECK (length(profile_sha256) = 64),
  profile_updated_at TEXT NOT NULL,
  unknown_fields_json TEXT NOT NULL CHECK (json_valid(unknown_fields_json)),
  required_categories_json TEXT NOT NULL CHECK (json_valid(required_categories_json)),
  registered_categories_json TEXT NOT NULL CHECK (json_valid(registered_categories_json)),
  catalog_categories_json TEXT NOT NULL CHECK (json_valid(catalog_categories_json)),
  missing_categories_json TEXT NOT NULL CHECK (json_valid(missing_categories_json)),
  errors_json TEXT NOT NULL CHECK (json_valid(errors_json)),
  processed_count INTEGER NOT NULL CHECK (processed_count >= 0),
  eligible_count INTEGER NOT NULL CHECK (eligible_count >= 0),
  needs_confirmation_count INTEGER NOT NULL CHECK (needs_confirmation_count >= 0),
  ineligible_count INTEGER NOT NULL CHECK (ineligible_count >= 0),
  current_campaigns INTEGER NOT NULL CHECK (current_campaigns >= 0),
  reference_campaigns INTEGER NOT NULL CHECK (reference_campaigns >= 0),
  upcoming_count INTEGER NOT NULL CHECK (upcoming_count >= 0),
  open_count INTEGER NOT NULL CHECK (open_count >= 0),
  closed_count INTEGER NOT NULL CHECK (closed_count >= 0),
  unknown_application_count INTEGER NOT NULL CHECK (unknown_application_count >= 0)
);

CREATE TABLE sources (
  source_id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  category TEXT NOT NULL CHECK (
    category IN (
      'civil_service',
      'institution',
      'military_civilian',
      'state_owned_enterprise'
    )
  ),
  cycle TEXT NOT NULL,
  selection_mode TEXT NOT NULL CHECK (
    selection_mode IN ('current', 'previous_reference')
  ),
  exam_at TEXT,
  portal_url TEXT NOT NULL,
  evidence_url TEXT NOT NULL,
  allowed_hosts_json TEXT NOT NULL CHECK (json_valid(allowed_hosts_json)),
  registration_opens_at TEXT,
  registration_closes_at TEXT
);

CREATE TABLE attachments (
  attachment_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('positions', 'reference')),
  format TEXT NOT NULL CHECK (
    format IN ('xlsx', 'xls', 'csv', 'tsv', 'zip')
  ),
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
  size INTEGER NOT NULL CHECK (size > 0)
);

CREATE TABLE positions (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
  category TEXT NOT NULL CHECK (
    category IN (
      'civil_service',
      'institution',
      'military_civilian',
      'state_owned_enterprise'
    )
  ),
  cycle TEXT NOT NULL,
  batch_status TEXT NOT NULL CHECK (
    batch_status IN ('current', 'previous_reference')
  ),
  application_status TEXT NOT NULL CHECK (
    application_status IN ('upcoming', 'open', 'closed', 'unknown')
  ),
  exam_at TEXT,
  title TEXT NOT NULL,
  organization TEXT NOT NULL,
  department TEXT NOT NULL,
  position_code TEXT NOT NULL,
  region TEXT NOT NULL,
  recruit_count INTEGER NOT NULL CHECK (recruit_count >= 0),
  requirements_json TEXT NOT NULL CHECK (json_valid(requirements_json)),
  requirement_states_json TEXT NOT NULL CHECK (json_valid(requirement_states_json)),
  eligibility TEXT NOT NULL CHECK (
    eligibility IN ('eligible', 'needs_confirmation', 'ineligible')
  ),
  match_reasons_json TEXT NOT NULL CHECK (json_valid(match_reasons_json)),
  confirmation_fields_json TEXT NOT NULL CHECK (json_valid(confirmation_fields_json)),
  exclusion_reasons_json TEXT NOT NULL CHECK (json_valid(exclusion_reasons_json)),
  decisions_json TEXT NOT NULL CHECK (json_valid(decisions_json)),
  registration_opens_at TEXT,
  registration_closes_at TEXT,
  attachment_id TEXT NOT NULL REFERENCES attachments(attachment_id),
  source_member TEXT NOT NULL,
  source_sheet TEXT NOT NULL,
  source_row INTEGER NOT NULL CHECK (source_row >= 1),
  preference_rank INTEGER NOT NULL CHECK (preference_rank >= 0),
  search_text TEXT NOT NULL
);

CREATE TABLE position_regions (
  position_id TEXT NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
  region_tag TEXT NOT NULL,
  PRIMARY KEY (position_id, region_tag)
);

CREATE INDEX idx_positions_feed ON positions (
  eligibility,
  category,
  source_id,
  batch_status,
  application_status,
  preference_rank,
  organization,
  position_code,
  id
);
CREATE INDEX idx_positions_eligibility ON positions (eligibility);
CREATE INDEX idx_positions_category ON positions (category);
CREATE INDEX idx_positions_source ON positions (source_id);
CREATE INDEX idx_positions_application ON positions (application_status);
CREATE INDEX idx_positions_batch ON positions (batch_status);
CREATE INDEX idx_position_regions_tag ON position_regions (region_tag, position_id);
