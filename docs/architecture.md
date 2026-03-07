# Pipeline Architecture

## Stages
1. **Harvest** via source adapters:
   - `ffsa`, `motorsport_uk`, `abkc` (tier 1)
   - `osm_overpass` (tier 2)
   - `venue_website` (tier 3)
2. **Normalize** evidence into `CandidateRecord` with strict schema.
3. **Deduplicate** with deterministic pair scoring and review queue.
4. **Entity resolution** by clustered normalized names + country.
5. **Decisioning** for accept/review/reject using reason codes.
6. **Geospatial enrichment** averaging trusted coordinates and creating point + working bbox.
7. **Outputs** with immutable run folder and run report/logs.

## Reason codes
Implemented codes include:
- confirmed_by_official_source
- confirmed_by_multiple_independent_sources
- outdoor_explicitly_stated
- karting_explicitly_stated
- osmtag_supports_karting
- venue_website_confirms_location
- probable_duplicate
- conflicting_coordinates
- indoor_only_evidence
- mixed_indoor_outdoor
- insufficient_evidence
- probably_closed
- clearly_closed
- temporary_event_only
- not_a_kart_track
- car_circuit_without_kart_track
- manual_review_required
