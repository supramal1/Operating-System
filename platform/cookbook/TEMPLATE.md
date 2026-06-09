# Cookbook Entry Template

Every cookbook entry follows this format. It is adapted from the xixu-me/prompt-library
entry structure, trimmed to what CO OS entries actually need. Copy the headings below
into a new file under `prompts/` (or `skills/`, once skills exist) and fill each one.
Keep it tight. An entry is a reusable pattern, not an essay.

---

# &lt;Title&gt;

One short line naming the pattern.

## Purpose

What the pattern does and why it exists: the problem it solves or the failure mode it
prevents. Two or three sentences.

## When to use

The conditions under which an agent should adopt this. Be specific about where it
applies and, where it matters, where it does not.

## The pattern

The reusable instruction itself, in the form an agent author can lift into a system
prompt or adapt. This is the load-bearing part of the entry. Where the proven wording
lives in another repo, summarise the pattern here and cite the source location rather
than duplicating large blocks.

## Example

A short worked example: an input and the output the pattern is meant to produce, or a
before-and-after showing the failure the pattern prevents.

## Variations

How the pattern flexes across agents or contexts. What stays fixed and what is allowed
to change when a different agent adopts it.

## Contracts it relates to

The CO OS contracts this pattern serves or is measured against (for example AC-1, AC-2,
AC-3). Name the contract and, in a few words, how the pattern relates to it. If no
contract enforces it, say so and name what does (for example an eval rubric dimension).

## Source

The agent or eval this pattern was proven in, with the file path or repo location. The
pattern is promoted here from proven material, never invented here.

## Version and date

`vX.Y` and the date the entry was written or last revised, ISO format.
