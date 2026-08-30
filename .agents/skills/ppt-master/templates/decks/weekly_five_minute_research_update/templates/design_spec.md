---
deck_id: weekly_five_minute_research_update
kind: deck
category: scenario
summary: A concise NTU-branded weekly research update system that makes milestone status, technical evidence, risks, and next commitments clear within five minutes.
keywords: [weekly-update, research, human-pose, evidence-led, ntu]
primary_color: "#D71440"
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
replication_mode: standard
native_structure_mode: structured
page_count: 10
placeholders:
  01_cover: ["{{SUBTITLE}}", "{{DATE}}", "{{AUTHOR}}"]
  02a_content_snapshot_milestone: ["{{KEY_MESSAGE}}", "{{STATUS}}", "{{MILESTONE}}", "{{SOURCE}}", "{{PAGE_NUM}}"]
  02b_content_technical_progress: ["{{TECHNICAL_PROGRESS}}", "{{CONTENT_AREA}}", "{{KEY_FINDING}}", "{{SOURCE}}", "{{PAGE_NUM}}"]
  02c_content_experimental_evidence: ["{{KEY_MESSAGE}}", "{{CONTENT_AREA}}", "{{FINDINGS}}", "{{SOURCE}}", "{{PAGE_NUM}}"]
  02d_content_risks_decisions: ["{{RISKS}}", "{{IMPACT}}", "{{MITIGATION}}", "{{DECISION_NEEDED}}", "{{PAGE_NUM}}"]
  02e_content_next_week: ["{{NEXT_ACTION_1}}", "{{NEXT_ACTION_2}}", "{{NEXT_ACTION_3}}", "{{OWNER_AND_DEADLINE}}", "{{PAGE_NUM}}"]
  02f_content_open_canvas: ["{{SOURCE}}", "{{PAGE_NUM}}"]
  02g_content_single_image_story: ["{{IMAGE_DESCRIPTION}}", "{{SOURCE}}", "{{PAGE_NUM}}"]
  02h_content_multi_image_story: ["{{CAPTION_1}}", "{{CAPTION_2}}", "{{CAPTION_3}}", "{{CAPTION_4}}", "{{SOURCE}}", "{{PAGE_NUM}}"]
  03_ending: []
---

# 5-Minute Weekly Research Update — Design Specification

## I. Template Overview

| Application context | Definition |
|---|---|
| Recurring presentation family | Weekly progress briefings for EE6008 Human Pose Analytics and similar evidence-led research projects. |
| Intended audiences and outcomes | The project supervisor, team members, and course reviewers should understand milestone health, completed work, experimental evidence, blockers, and the next measurable commitments within five minutes. |
| Delivery and reading assumptions | Primarily presented live, with enough written evidence and source space to remain useful when handed off after the meeting. |
| Representative narrative/page roles | Weekly snapshot, milestone tracking, technical progress, experimental evidence, controlled comparison, risk and decision framing, next-week commitments, open-canvas explanation, image-led evidence, and a concise close. |

- Tone: academic, concise, technical, and evidence-led.
- Theme: predominantly light, with NTU Red for conclusions and exceptions and NTU Blue for structure, navigation, and analytical context.
- Research context: instance-preserving pose representation for multi-person action recognition, with emphasis on person identity, relative geometry, controlled evaluation, and parameter-conscious comparisons.

## II. Color Scheme

| Role | HEX | Template-specific use |
|---|---|---|
| NTU Red | `#D71440` | Primary identity rail, decisive takeaway, critical risk, and active milestone. |
| NTU Blue | `#181C62` | Footer band, analytical structure, technical labels, and comparison anchors. |
| White | `#FFFFFF` | Main canvas and logo clearance field. |
| Pale Blue | `#EEF1FA` | Technical and evidence zones that need quiet separation. |
| Pale Red | `#FCE9EE` | Risk, decision, or exception fields. |
| Cool Grey | `#E6E6E6` | Dividers, inactive milestones, and low-priority framing. |
| Dark Text | `#20243A` | Primary text on light fields. |
| Muted Text | `#5E6478` | Metadata, source notes, and secondary explanation. |

Red and blue remain visually distinct through labels, position, and boundary treatment; status meaning is never communicated by color alone.

## III. Typography

- Export face: Arial for portable English-language PowerPoint delivery.
- Titles use Arial Bold; body, metadata, and source notes use Arial Regular.
- The NTU master logo remains artwork and is never reconstructed with text.
- Body baseline: 22 px for ordinary projected content; metadata may use 13–16 px when confined to the footer or source line.

## IV. Signature Design Elements

- A narrow NTU Red rail fixes the left edge, while a deep NTU Blue footer creates a consistent presentation frame.
- The NTU master logo sits in a clear white field at the upper-right with a width above the official digital minimum and an exclusion zone around the crest.
- Analytical pages use one dominant evidence region plus one supporting interpretation region. Dedicated image-story layouts provide editable sample photography that can be replaced with research figures, qualitative results, implementation screenshots, or annotated evidence.
- Milestones use a horizontal checkpoint line with clearly labelled current and upcoming states.
- Risk pages pair pale-red risk fields with a blue decision field so problems and requested actions remain visually separate.
- Campus photography defines the cover and closing compositions and supplies replaceable preview imagery for the image-story layouts. The cover uses a wide, semi-transparent architectural image field whose top and bottom align with the left red marker, extends into the text-side composition, and remains an editable slide-local module with an editable white handoff and red diagonal accent; the closing page uses a white-washed full-background photograph of the NTU EEE S2 building with dark-blue central typography.
- Content prototypes include editable preset labels, status options, evidence prompts, and output-oriented helper text so a first-time user can populate the weekly update without reverse-engineering each region.

## V. Page Roster

| SVG | Layout key | PowerPoint picker name | Intended role, visual character, slots, and structural capacity |
|---|---|---|---|
| `01_cover.svg` | `weekly-cover` | `Weekly Update — Cover` | Branded opening with a wide semi-transparent panoramic exterior view of The Hive, vertically aligned to the red marker and extended left for visual interaction with the research title zone. The photograph, white blend, and red diagonal accent form one editable slide-local module; the week/date and presenter remain editable text slots. |
| `02a_content_snapshot_milestone.svg` | `weekly-snapshot` | `Weekly Update — Snapshot & Milestone` | One-sentence weekly conclusion, status badge, current milestone, and a six-checkpoint schedule rail. Supports fast orientation before technical detail. |
| `02b_content_technical_progress.svg` | `weekly-technical-progress` | `Weekly Update — Technical Progress` | Left progress narrative, central pipeline or architecture object area, and a highlighted technical finding. Supports method, implementation, or data-pipeline updates. |
| `02c_content_experimental_evidence.svg` | `weekly-experimental-evidence` | `Weekly Update — Experimental Evidence` | Dominant object area for one chart, table, confusion matrix, or controlled comparison, paired with a concise takeaway and findings column. |
| `02d_content_risks_decisions.svg` | `weekly-risks-decisions` | `Weekly Update — Risks & Decisions` | Separate risk, impact, mitigation, and decision-needed regions. Supports escalation without mixing the problem statement with the requested action. |
| `02e_content_next_week.svg` | `weekly-next-week` | `Weekly Update — Next-Week Commitments` | Three sequential commitment lanes plus an owner/deadline field. Supports measurable outputs rather than broad activity lists. |
| `02f_content_open_canvas.svg` | `weekly-open-canvas` | `Weekly Update — Open Canvas` | A titled content page that retains only the NTU frame and one large outlined blank canvas. It provides maximum freedom for editable diagrams, equations, tables, or content assembled directly in PowerPoint. |
| `02g_content_single_image_story.svg` | `weekly-single-image-story` | `Weekly Update — Single-Image Story` | One dominant editable picture placeholder paired with a compact description panel. Suitable for an annotated result, qualitative example, architecture overview, implementation screenshot, or project photograph. |
| `02h_content_multi_image_story.svg` | `weekly-multi-image-story` | `Weekly Update — Multi-Image Story` | Four editable picture placeholders arranged as a 2 × 2 story grid with individual captions. Users may retain the first two, first three, or all four image cards according to the available evidence. |
| `03_ending.svg` | `weekly-ending` | `Weekly Update — Closing` | Full-background exterior view of the NTU EEE S2 building with one large editable closing title centered on the page. |

## VI. Assets

| File | Dimensions | Intended usage and provenance |
|---|---:|---|
| `images/ntu_master_logo.png` | 3006 × 1079 | Official master logo served by the NTU website. Use unaltered on a clear background; institutional-use authorization remains the user's responsibility. |
| `images/the_hive_ntu_ccby4.jpg` | 6646 × 4431 | High-resolution cover photograph of The Hive by Supanut Arunoprayote, licensed CC BY 4.0; attribution and license link must remain in project source records. |
| `images/the_hive_ntu_exterior_official.jpg` | 5020 × 3012 | Official NTU exterior photograph of The Hive used as the semi-transparent cover background. Source: NTU Singapore website. |
| `images/the_hive_ntu_exterior_cover_crop.jpg` | 1830 × 1465 | Presentation-optimized portrait crop derived from the official NTU exterior photograph; retained in the candidate image library for future layouts. |
| `images/the_hive_ntu_exterior_cover_wide.jpg` | 2200 × 1025 | Presentation-optimized wide crop derived from the official NTU exterior photograph; used by the editable cover image module. |
| `images/gaia_nbs_official.jpg` | 1119 × 746 | Official NTU NBS image of Gaia / Wee Cho Yaw Plaza for closing-page campus context. |
| `images/eee_official_collage.png` | 933 × 740 | Official NTU EEE technology collage for a restrained closing-page thumbnail or later project-specific reuse. |
| `images/eee_building_exterior_full_bleed.jpg` | 1893 × 1035 | Presentation-optimized crop of the official NTU EEE S2 building exterior photograph; used as the closing-page background. Source: NTU EEE website. |

## VII. Placeholder Overrides

The weekly-update layouts extend the canonical vocabulary with explicit status, milestone, evidence, risk, mitigation, decision, action, owner, and deadline roles. These markers make the recurring research-reporting contract discoverable while preserving ordinary PowerPoint placeholder types underneath.
