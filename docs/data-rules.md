# Validation Rules

These are the rules that `POST /validate-annotations` applies to an import file. They come from the "Data rules" and "AutoQA rule" sections of the exercise brief.

There are three kinds of rule:

- **Type rules**: a field exists and has the correct type.
- **Content rules**: a value is correct by itself, or in relation to other fields.
- **AutoQA rules**: a quality check across the valid annotations in one frame. These produce warnings, not errors.

Type and content rules produce validation errors. The type/content split organises the validator's code and is not sent in the response.

## Trusted inputs

`images`, `allowed_labels` and `label_subsets` are trusted reference data supplied with each request, and none of them is validated:

- Image ids are unique, and image dimensions are positive integers.
- Allowed labels are unique, non-empty strings.
- `label_subsets` is an array of non-empty arrays of allowed labels. No label repeats within a subset or across subsets.

## Type rules

| ID | Rule |
|----|------|
| T1 | Each annotation is an object. |
| T2 | `id` is present and is a string. |
| T3 | `image_id` is present and is a string. |
| T4 | `label` is present and is a string. |
| T5 | `box` is present and is an object. |
| T6 | `box.x`, `box.y`, `box.width` and `box.height` are each present and are JSON numbers. Booleans and numeric strings (`true`, `"10"`) are not numbers. |

## Content rules

### One value checked by itself

| ID | Rule |
|----|------|
| C1 | `id` is not an empty string. |
| C2 | `box.x` and `box.y` are finite and greater than or equal to 0. |
| C3 | `box.width` and `box.height` are finite and greater than 0. |

`NaN`, `Infinity` and `-Infinity` are accepted when the request is parsed, so C2 and C3 must check finiteness explicitly.

### A value checked against other fields

| ID | Rule |
|----|------|
| C4 | `id` is unique among the annotations in the request. |
| C5 | `image_id` matches the id of an entry in `images`. |
| C6 | `label` exactly matches an entry in `allowed_labels`: case-sensitive, with no trimming. |
| C7 | The box fits inside its image: `x + width <= image.width` and `y + height <= image.height`. Touching the right or bottom edge is valid. Fractional coordinates are allowed. |

C7 applies only when T6, C2, C3 and C5 pass, because it needs valid numbers and an image that exists.

## AutoQA rules

| ID | Rule |
|----|------|
| Q1 | **Mutually exclusive label subsets.** For each frame, collect the distinct labels from that frame's valid annotations. A subset is present if any of its labels appears. If two or more subsets are present, return a warning. |

How Q1 behaves:

- **Only valid annotations count:** those that pass every type and content rule.
- **Duplicate labels don't count twice.** Two annotations with the same label activate that label's subset once.
- **A subset need not be complete.** One of its labels is enough to make it present.
- **Labels in no subset are ignored.**
- **Each frame is checked on its own.** Different subsets in different frames don't conflict.
- **An empty `label_subsets` turns the check off.**

Example, with subsets `[["instrument", "grasper"], ["tissue", "organ"]]`:

| Labels in one frame | Outcome |
|---------------------|---------|
| `instrument`, `grasper` | No warning: same subset |
| `instrument`, `tissue` | Warning: two subsets present |
| `instrument` | No warning |
| A label in no subset | No warning |
| No labels | No warning |

A warning must name the frame and say which observed labels and which subsets conflict, so a user can review those annotations.

## General behavior

- **Every problem is reported**, including several on one annotation.
- **Nothing is coerced, repaired or removed.** An invalid record stays in the file and its errors are reported.
- **Unexpected fields are ignored.**
- **Overlapping boxes are allowed.** There is no overlap check.
- **Out of scope for this prototype:** checking the request's top-level shape (for example, that `annotations` is a list).

## Assumptions

- **A "frame" is an entry in `images`,** so Q1 groups annotations by `image_id`.
