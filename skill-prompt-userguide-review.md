# 📖 User Guide Review Master Skill

> **Transform documentation from confusing to crystal-clear. Ensure every user guide is accurate, complete, and genuinely helpful.**

---

## 📋 Overview

This skill provides a comprehensive framework for reviewing user guides, manuals, and documentation with the precision of a technical writer and the empathy of a user advocate. Whether you're validating help docs, onboarding guides, or API references, this guide ensures your documentation serves its users effectively.

**What You'll Master:**
- ✅ Accuracy validation against system behavior
- 📋 Completeness verification (prerequisites, errors, edge cases)
- 🎨 Usability and clarity assessment
- 🔗 Consistency checking across documents
- ⚡ Structured review workflows

---

## 🚀 Quick Start

### The Review Workflow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  INTAKE         │───▶│  COMPARE        │───▶│  EVALUATE       │───▶│  REPORT         │
│  Gather Docs    │    │  Against Source │    │  Quality &      │    │  Findings &     │
│  & Context      │    │  of Truth       │    │  Usability      │    │  Improvements   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Phase 1: Intake** - Collect user guide, requirements, and test artifacts  
**Phase 2: Compare** - Validate against requirements and test behavior  
**Phase 3: Evaluate** - Check completeness, clarity, and consistency  
**Phase 4: Report** - Document issues with specific corrections

---

## 🏛️ Core Review Frameworks

### 1. The A.C.C.U.R.A.T.E. Framework

Comprehensive documentation evaluation:

| Component | What to Check | Review Questions |
|-----------|---------------|------------------|
| **A**ccuracy | Information is correct | Does this match system behavior? |
| **C**ompleteness | Nothing missing | Are all features documented? |
| **C**larity | Easy to understand | Would a new user understand this? |
| **U**sability | Practical and helpful | Can users follow these steps? |
| **R**elevance | Appropriate for audience | Is this information necessary? |
| **A**ccessibility | Available to all users | Are WCAG guidelines followed? |
| **T**imeliness | Current and versioned | Is this for the right version? |
| **E**xamples | Concrete illustrations | Are there sufficient examples? |

### 2. The U.S.E.R. Method

User-centered review approach:

- **U**nderstand: Who is the audience? (beginner, expert, admin?)
- **S**tep-through: Actually follow the documented steps
- **E**valuate: Does it achieve the stated goal?
- **R**eview: Check against requirements and test cases

### 3. The D.O.C.U.M.E.N.T. Checklist

Multi-dimensional quality assessment:

| Dimension | Description | Verification Method |
|-----------|-------------|---------------------|
| **D**iscoverable | Easy to find and navigate | Check TOC, search, links |
| **O**rganized | Logical structure | Review information architecture |
| **C**orrect | Factually accurate | Cross-reference with system |
| **U**p-to-date | Current version | Check against release notes |
| **M**easurable | Clear success criteria | Verify expected outcomes |
| **E**xhaustive | Covers all scenarios | Check edge cases and errors |
| **N**avigable | Clear progression | Step through instructions |
| **T**raceable | Links to requirements | Map to REQ and TC IDs |

---

## 📥 Input Requirements

### Required Artifacts

```
📁 Review Package Structure
├── 📖 User Guide/
│   ├── Complete guide (PDF/DOCX/HTML/MD)
│   ├── Specific section focus (optional)
│   └── Version information
├── 📋 Requirements/
│   ├── JIRA/ValueEdge tickets
│   ├── Feature specifications
│   └── Acceptance criteria
├── 🧪 Test Artifacts/
│   ├── Test cases (.feature/.xlsx)
│   ├── Expected system behavior
│   └── Known issues/limitations
├── 🎯 Context/
│   ├── Target audience definition
│   ├── User personas
│   └── Use cases
└── ⚙️ Configuration/
    ├── Review focus areas
    ├── Style guide references
    └── Terminology glossary
```

### Minimum Viable Input

For an effective review, you need:

1. **User Guide** (primary document)
   - [ ] Complete guide or specific section
   - [ ] Current version
   - [ ] Format (PDF, DOCX, HTML, Markdown)

2. **Source of Truth** (at least one)
   - [ ] Requirements (JIRA/ValueEdge/PRD)
   - [ ] Test cases showing expected behavior
   - [ ] Working system for verification
   - [ ] Subject matter expert access

3. **Context**
   - [ ] Target audience level
   - [ ] Product version
   - [ ] Known limitations

---

## 🔍 Mandatory Review Checks

### Check 1: Accuracy Validation

Verify every statement against system behavior:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACCURACY VALIDATION CHECKLIST                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ □ WORKFLOW ACCURACY                                                          │
│   ├── Steps are in correct order                                             │
│   ├── Navigation paths match actual UI                                       │
│   ├── Button/field names match interface                                     │
│   ├── Screenshots reflect current UI                                         │
│   └── Behavior matches test case expectations                                │
│                                                                              │
│ □ FUNCTIONAL ACCURACY                                                        │
│   ├── Feature descriptions match implementation                              │
│   ├── Configuration values are correct                                       │
│   ├── Default settings are accurate                                          │
│   ├── Output formats match reality                                           │
│   └── API endpoints/parameters are correct                                   │
│                                                                              │
│ □ BUSINESS RULE ACCURACY                                                     │
│   ├── Validation rules match system behavior                                 │
│   ├── Permission requirements are correct                                    │
│   ├── Limits and thresholds are accurate                                     │
│   └── Calculation formulas are correct                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Accuracy Verification Matrix

| Guide Section | Source of Truth | Verification Status | Notes |
|---------------|-----------------|---------------------|-------|
| Login Process | TC-AUTH-001 | ✅ Verified | Matches test |
| Report Generation | REQ-045 | ⚠️ Partial | Missing error scenario |
| User Import | Tested in Sprint 5 | ❌ Outdated | UI changed in v2.1 |
| API Setup | API Spec v2.0 | ✅ Verified | Documentation current |

### Check 2: Completeness Assessment

#### The Complete Documentation Pyramid

```
                        ▲
                       /█\        ADVANCED TOPICS
                      /███\       • Configuration
                     /█████\      • Customization
                    /███████\     • Integration
                   /█████████\
                  /███████████\   TROUBLESHOOTING
                 /█████████████\  • Common errors
                /███████████████\ • FAQ
               /█████████████████\• Support contacts
              /███████████████████\
             ───────────────────────
            /███████████████████████\ HOW-TO GUIDES
           /█████████████████████████\• Step-by-step
          /███████████████████████████\• Workflows
         /█████████████████████████████\• Examples
        /─────────────────────────────────\
       /███████████████████████████████████\ CORE CONCEPTS
      /█████████████████████████████████████\• Overview
     /███████████████████████████████████████\• Terminology
    /───────────────────────────────────────────\
   /█████████████████████████████████████████████\ PREREQUISITES
  /███████████████████████████████████████████████\• Requirements
 /█████████████████████████████████████████████████\• Setup
/─────────────────────────────────────────────────────\
                     FOUNDATION
```

#### Completeness Checklist by Section Type

**Getting Started Section:**
- [ ] System requirements (hardware, software, browser)
- [ ] Installation/setup instructions
- [ ] Initial configuration steps
- [ ] First-time user walkthrough
- [ ] Quick start summary

**Feature Documentation:**
- [ ] What the feature does (purpose)
- [ ] When to use it (use cases)
- [ ] How to access it (navigation)
- [ ] How to use it (step-by-step)
- [ ] Expected outcomes/results
- [ ] Related features

**Configuration/Admin:**
- [ ] Available settings/options
- [ ] Default values and implications
- [ ] Configuration recommendations
- [ ] Impact of different settings
- [ ] Security considerations

**API Documentation:**
- [ ] Endpoint descriptions
- [ ] Request format (method, URL, headers)
- [ ] Request body schema (with types)
- [ ] Response format (success and error)
- [ ] Authentication requirements
- [ ] Rate limiting information
- [ ] Code examples (multiple languages)

**Troubleshooting:**
- [ ] Common error messages
- [ ] Causes and explanations
- [ ] Step-by-step solutions
- [ ] Prevention tips
- [ ] When to contact support

### Check 3: Usability Evaluation

#### Usability Heuristics for Documentation

| Heuristic | Check | Pass Criteria |
|-----------|-------|---------------|
| **Visibility** | Can users find what they need? | Clear TOC, search, navigation |
| **Match** | Does language match user mental model? | Terms match user vocabulary |
| **Control** | Can users recover from mistakes? | Error handling documented |
| **Consistency** | Is formatting/presentation uniform? | Same style throughout |
| **Recognition** | Is information easy to digest? | Scannable, chunked content |
| **Efficiency** | Can experts work quickly? | Shortcuts, advanced tips |
| **Aesthetics** | Is it pleasant to read? | Clean layout, good typography |
| **Help** | Is assistance available? | Contextual help, examples |

#### Readability Scorecard

| Aspect | Criteria | Score |
|--------|----------|-------|
| **Sentence Length** | Average < 20 words | /5 |
| **Paragraph Length** | 3-5 sentences max | /5 |
| **Active Voice** | > 80% active sentences | /5 |
| **Jargon** | Defined or avoided | /5 |
| **Headings** | Clear hierarchy (H1→H2→H3) | /5 |
| **Lists** | Used for steps/options | /5 |
| **Examples** | Concrete, relevant | /5 |
| **Visuals** | Screenshots, diagrams where helpful | /5 |

**Total: __/40**

- 35-40: Excellent
- 28-34: Good
- 20-27: Needs improvement
- <20: Requires rewrite

### Check 4: Consistency Verification

#### Cross-Document Consistency

| Element | Check Across | Consistency Rule |
|---------|--------------|------------------|
| **Terminology** | All docs, UI, code | Same term = same concept |
| **Product Names** | All documents | Exact spelling, capitalization |
| **UI Labels** | Guide and actual UI | Match exactly (case-sensitive) |
| **Version Numbers** | Guide, requirements, release notes | Align with current release |
| **Procedures** | Guide and test cases | Steps match expected behavior |
| **Error Messages** | Guide and system | Exact text match |

#### Internal Consistency Checklist

- [ ] Heading levels follow logical hierarchy
- [ ] Formatting is consistent (fonts, colors, spacing)
- [ ] Numbering style is uniform (1. 2. 3. vs Step 1, Step 2)
- [ ] Voice is consistent (active vs passive)
- [ ] Tense is consistent (present tense preferred)
- [ ] Person is consistent ("you" vs "the user")
- [ ] Code formatting is uniform
- [ ] Callout styles are consistent (Note, Warning, Tip)

### Check 5: Version Alignment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VERSION ALIGNMENT MATRIX                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Document: [Guide Name]                      Version: [Doc Version]           │
│ Last Updated: [Date]                        Review Date: [Date]              │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Product Versions:                                                            │
│ □ Guide version matches current product version: [Version]                   │
│ □ Documented features exist in current version                               │
│ □ Deprecated features are marked as such                                     │
│ □ New features since last update are documented                              │
│                                                                              │
│ Requirement Alignment:                                                       │
│ □ All documented features link to requirements                               │
│ □ Requirement status matches feature availability                            │
│ □ Scope boundaries are clear                                                 │
│                                                                              │
│ Test Case Alignment:                                                         │
│ □ Documented workflows match test case steps                                 │
│ □ Expected results in guide match test assertions                            │
│ □ Error scenarios in guide match test cases                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Review Output Structure

### Executive Summary

```markdown
# User Guide Review Report

## 📋 Document Information
- **Document:** [Guide Name]
- **Version:** [X.Y]
- **Pages/Sections:** [Count]
- **Review Date:** [Date]
- **Reviewer:** [Name]

## 🏥 Health Score
| Category | Score | Status |
|----------|-------|--------|
| Accuracy | 8.2/10 | 🟢 Good |
| Completeness | 7.5/10 | 🟡 Acceptable |
| Usability | 8.8/10 | 🟢 Good |
| Consistency | 9.0/10 | 🟢 Good |
| **OVERALL** | **8.4/10** | 🟢 GOOD |

## 🎯 Critical Findings
1. **HIGH**: Section 3.2 describes deprecated feature (removed in v2.1)
2. **HIGH**: API endpoint /v1/users is incorrect (should be /v2/users)
3. **MEDIUM**: Missing error handling for timeout scenario
4. **MEDIUM**: Prerequisites section incomplete (missing browser versions)
5. **LOW**: Inconsistent capitalization of product name (3 instances)

## 📊 Statistics
- **Total Issues Found:** 23
- **Critical:** 2
- **High:** 5
- **Medium:** 10
- **Low:** 6
- **Action Items:** 18

## ✅ Recommendations Summary
- **Rewrite:** 2 sections (deprecated content)
- **Update:** 8 sections (accuracy issues)
- **Add:** 4 sections (missing content)
- **Format:** 4 items (consistency)
```

### Section-by-Section Review

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ SECTION REVIEW: [Section Name]                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Metadata:                                                                    │
│ • Pages: [X] to [Y]                                                          │
│ • Requirements Covered: [REQ-001, REQ-002]                                   │
│ • Test Cases Referenced: [TC-001, TC-002]                                    │
│                                                                              │
│ Accuracy Review:                                                             │
│ ✅ Correct: [List of accurate statements]                                    │
│ ⚠️  Partial: [List of partially correct content]                             │
│ ❌ Incorrect: [List of inaccurate content]                                   │
│                                                                              │
│ Completeness Review:                                                         │
│ ✅ Present: [What is documented]                                             │
│ ❌ Missing: [What should be added]                                           │
│                                                                              │
│ Usability Review:                                                            │
│ Score: [X]/10                                                                │
│ Strengths: [What's good]                                                     │
│ Improvements: [What could be better]                                         │
│                                                                              │
│ Specific Corrections:                                                        │
│ 1. [Original text] → [Corrected text]                                        │
│ 2. [Original text] → [Corrected text]                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Issues Register

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ISSUES REGISTER                                                              │
├──────────┬────────┬────────────────┬───────────────────┬─────────────────────┤
│ Issue ID │ Severity │ Section        │ Issue Type        │ Description         │
├──────────┼────────┼────────────────┼───────────────────┼─────────────────────┤
│ UG-001   │ HIGH   │ 2.3 Login      │ Accuracy          │ Step 2 says click   │
│          │        │                │                   │ "Sign In" but button│
│          │        │                │                   │ label is "Login"    │
├──────────┼────────┼────────────────┼───────────────────┼─────────────────────┤
│ UG-002   │ CRIT   │ 4.1 API        │ Version           │ Endpoint /v1/users  │
│          │        │ Reference      │ Mismatch          │ deprecated, should  │
│          │        │                │                   │ be /v2/users        │
├──────────┼────────┼────────────────┼───────────────────┼─────────────────────┤
│ UG-003   │ MED    │ 3.5 Export     │ Missing Content   │ No troubleshooting  │
│          │        │                │                   │ for timeout error   │
├──────────┼────────┼────────────────┼───────────────────┼─────────────────────┤
│ UG-004   │ LOW    │ Throughout     │ Consistency       │ "Admin Panel" vs    │
│          │        │                │                   │ "Admin Console"     │
└──────────┴────────┴────────────────┴───────────────────┴─────────────────────┘
```

### Action Plan

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ CORRECTION ACTION PLAN                                                       │
├──────────┬────────────────────────────────────────┬──────────┬───────────────┤
│ Priority │ Correction Required                    │ Owner    │ Due Date      │
├──────────┼────────────────────────────────────────┼──────────┼───────────────┤
│ P0       │ Update API endpoint in Section 4.1     │ Tech     │ 2024-01-12    │
│          │ from /v1/users to /v2/users            │ Writer   │               │
├──────────┼────────────────────────────────────────┼──────────┼───────────────┤
│ P0       │ Remove Section 3.2 (deprecated         │ Doc      │ 2024-01-12    │
│          │ feature) or mark as legacy             │ Lead     │               │
├──────────┼────────────────────────────────────────┼──────────┼───────────────┤
│ P1       │ Add timeout troubleshooting to         │ Tech     │ 2024-01-18    │
│          │ Section 3.5                            │ Writer   │               │
├──────────┼────────────────────────────────────────┼──────────┼───────────────┤
│ P1       │ Standardize product name               │ Doc      │ 2024-01-16    │
│          │ throughout document                    │ Editor   │               │
├──────────┼────────────────────────────────────────┼──────────┼───────────────┤
│ P2       │ Add browser version requirements       │ Tech     │ 2024-01-25    │
│          │ to prerequisites section               │ Writer   │               │
└──────────┴────────────────────────────────────────┴──────────┴───────────────┘
```

---

## ❓ Clarification Protocol

### When to Request Clarification

Trigger clarification requests when encountering:

| Scenario | Example | Question Template |
|----------|---------|-------------------|
| **Missing Prerequisites** | Guide jumps into advanced topic | "What knowledge or setup should users have before attempting this?" |
| **Undocumented Features** | Guide mentions feature not in requirements | "Section X describes [feature] not listed in requirements. Should this be documented?" |
| **Version Uncertainty** | URL or version info unclear | "This guide references v1.2 API, but latest is v2.0. Which version should I validate against?" |
| **Test Case Conflict** | Guide steps differ from test cases | "Guide says to click X, but test case TC-Y expects button Y. Which is correct?" |
| **Unclear Audience** | Tone/depth seems inconsistent | "Who is the target audience? Technical administrators or end users?" |
| **Scope Ambiguity** | Unclear what is/is not covered | "Should this guide cover [topic], or is that documented separately?" |

### Clarification Request Format

```markdown
## 🙋 Clarification Needed

**Question [X/5]:** [Clear, specific question]

**Context:** 
- **Document:** [Guide Name], Section [X.Y]
- **Requirement:** [REQ-ID] (if applicable)
- **Test Case:** [TC-ID] (if applicable)
- **Specific Issue:** [What exactly is unclear]

**Current Text:**
> "[Quote the ambiguous text]"

**Options (if applicable):**
- Option A: [Description]
- Option B: [Description]

**Impact:** [How this affects the review - blocking/partial/minimal]
```

### Quality Gates for Questions

- ✅ Ask at most 5 clarification questions per round
- ✅ Prioritize blocking questions first
- ✅ Include document snippets (quote relevant text)
- ✅ Suggest possible interpretations when applicable
- ✅ Track asked questions to avoid duplicates
- ✅ Group related questions by section

---

## 🎨 Document Type-Specific Reviews

### User Manual / Getting Started Guide

```
Review Checklist for User Manuals:

□ First-Time Experience
  ├── Prerequisites are clear and complete
  ├── Installation/setup steps work end-to-end
  ├── First login/initialization covered
  ├── Quick tour or orientation provided
  └── Common first actions documented

□ Task-Oriented Structure
  ├── Organized by user goals (not features)
  ├── Each task has clear outcome
  ├── Steps are numbered and actionable
  ├── Screenshots match current UI
  └── Expected results are verifiable

□ Progressive Disclosure
  ├── Basic tasks covered first
  ├── Advanced topics clearly marked
  ├── Prerequisites link to earlier sections
  └── No forward references without links

□ Help & Support
  ├── FAQ section included
  ├── Error scenarios addressed
  ├── Support contact information
  └── Related resources linked
```

### API Documentation

```
Review Checklist for API Docs:

□ Endpoint Reference
  ├── All endpoints documented
  ├── HTTP methods correct
  ├── URL patterns accurate
  ├── Authentication requirements clear
  └── Rate limiting specified

□ Request Specification
  ├── All parameters listed
  ├── Required vs optional marked
  ├── Data types specified
  ├── Valid values/enums documented
  └── Example request provided

□ Response Specification
  ├── Success response schema
  ├── All error responses documented
  ├── Status codes explained
  ├── Response headers documented
  └── Example responses provided

□ Code Samples
  ├── Multiple language examples
  ├── Samples are runnable
  ├── Authentication included
  └── Error handling shown

□ Changelog
  ├── Version history maintained
  ├── Breaking changes highlighted
  ├── Deprecation notices included
  └── Migration guides provided
```

### Administrator Guide

```
Review Checklist for Admin Guides:

□ Installation & Setup
  ├── System requirements detailed
  ├── Installation procedures step-by-step
  ├── Configuration options explained
  ├── Security hardening guidelines
  └── Verification steps included

□ Configuration Reference
  ├── All settings documented
  ├── Default values listed
  ├── Configuration file examples
  ├── Environment variables covered
  └── Best practices included

□ Maintenance Procedures
  ├── Backup/restore processes
  ├── Upgrade procedures
  ├── Monitoring guidance
  ├── Troubleshooting common issues
  └── Performance optimization

□ Security
  ├── Authentication setup
  ├── Authorization configuration
  ├── SSL/TLS configuration
  ├── Audit logging
  └── Compliance considerations
```

### Release Notes

```
Review Checklist for Release Notes:

□ Version Information
  ├── Version number prominent
  ├── Release date included
  ├── Compatibility information
  └── Upgrade requirements

□ New Features
  ├── Each feature described
  ├── Value proposition clear
  ├── Link to detailed docs
  └── Known limitations noted

□ Bug Fixes
  ├── Issue reference numbers
  ├── Brief description of fix
  └── Impact on users

□ Breaking Changes
  ├── Clearly marked/highlighted
  ├── Migration steps provided
  ├── Deprecation timeline
  └── Alternative approaches

□ Known Issues
  ├── Current limitations listed
  ├── Workarounds provided
  ├── Planned fixes mentioned
  └── Support escalation path
```

---

## 📋 Review Templates

### Template 1: Quick Documentation Check

```markdown
# Quick Doc Review

## Document: [Name]
## Version: [X.Y]

## Quick Checks
- [ ] Accurate: Steps match current system
- [ ] Complete: Prerequisites, steps, results included
- [ ] Clear: Easy to follow
- [ ] Current: Matches product version

## Red Flags
- [ ] Any blocking inaccuracies?
- [ ] Missing critical sections?
- [ ] Outdated screenshots?

## Verdict
- [ ] ✅ APPROVED - Ready to publish
- [ ] ⚠️ APPROVED WITH EDITS - Minor fixes needed
- [ ] ❌ NEEDS WORK - Significant revisions required

## If Edits Needed:
1. [List required changes]
```

### Template 2: Comprehensive Documentation Audit

```markdown
# Comprehensive Documentation Audit

## 1. Document Profile
| Attribute | Value |
|-----------|-------|
| Document Name | |
| Version | |
| Page Count | |
| Target Audience | |
| Last Updated | |

## 2. Coverage Analysis
| Feature Area | Documented | Accurate | Complete |
|--------------|------------|----------|----------|
| Feature A | Y/N | Y/N | Y/N |
| Feature B | Y/N | Y/N | Y/N |

## 3. Quality Assessment
| Criteria | Score (1-5) | Notes |
|----------|-------------|-------|
| Accuracy | | |
| Completeness | | |
| Clarity | | |
| Organization | | |
| Visual Design | | |

## 4. Issues Summary
| Severity | Count | Examples |
|----------|-------|----------|
| Critical | | |
| High | | |
| Medium | | |
| Low | | |

## 5. Recommendations
### Immediate Actions
1. [Critical fixes]

### Short-term Improvements
1. [High priority enhancements]

### Long-term Enhancements
1. [Strategic improvements]

## 6. Sign-off
| Role | Name | Date | Approved |
|------|------|------|----------|
| Technical Reviewer | | | |
| Documentation Lead | | | |
| Product Owner | | | |
```

### Template 3: Comparison Review

```markdown
# Guide vs System Comparison Review

## Method
Following documented steps in real system environment

## Environment
- Product Version: [X.Y.Z]
- Browser/OS: [Details]
- Test Date: [Date]

## Section-by-Section Comparison

### Section [X]: [Title]
| Step | Guide Says | System Does | Match? |
|------|------------|-------------|--------|
| 1 | | | ✅/❌ |
| 2 | | | ✅/❌ |
| 3 | | | ✅/❌ |

**Result:** [Accurate/Needs Update]
**Notes:** [Observations]

## Summary
- Sections Accurate: [X]/[Y]
- Sections Needing Update: [Z]
- Critical Discrepancies: [N]
```

---

## 🏆 Best Practices

### The Golden Rules of Documentation Review

1. **Review with Fresh Eyes** - Approach as a new user would
2. **Follow Every Step** - Actually perform documented actions
3. **Question Everything** - Verify every fact, link, and reference
4. **Think of the User** - Consider their knowledge level and goals
5. **Check the Source** - Validate against requirements and system
6. **Version Matters** - Ensure alignment with current release
7. **Consistency is Key** - Same terms, same formatting, same voice
8. **Examples are Essential** - Abstract concepts need concrete illustrations

### Review Anti-Patterns to Avoid

| Anti-Pattern | Why It Is Harmful | Better Approach |
|--------------|-------------------|-----------------|
| **Skimming** | Misses subtle inaccuracies | Read every word, follow every step |
| **Assuming Knowledge** | What is obvious to you may not be to users | Review from beginner perspective |
| **Ignoring Formatting** | Poor formatting hurts usability | Check visual presentation |
| **Version Blindness** | Docs for wrong version mislead users | Verify version alignment first |
| **No Ground Truth** | Cannot verify without source | Always have requirements/tests to compare |
| **Surface Review** | Deep issues remain hidden | Test every procedure end-to-end |

### Documentation Quality Metrics

**Accuracy Metrics:**
- Factual Accuracy: (Verified statements / Total statements) × 100
- Version Alignment: Correct version references / Total references
- Test Coverage: Documented features with passing tests / Total features

**Usability Metrics:**
- Task Completion Rate: Users completing task with docs / Total users
- Time to Information: Average time to find specific info
- Error Rate: Users making errors following docs / Total attempts

**Completeness Metrics:**
- Feature Coverage: Documented features / Total features
- Scenario Coverage: Documented scenarios / Required scenarios
- Error Coverage: Documented errors / Known errors

---

## 🎯 Quick Reference Card

### The Review Formula

```
[ACCURACY] + [COMPLETENESS] + [USABILITY] + [CONSISTENCY] = ✅ PUBLISH READY
```

### One-Liner Review Boosters

Add these to any review prompt:

- "Focus on steps that could cause user errors"
- "Flag any UI labels that do not match the interface"
- "Identify missing prerequisites for each procedure"
- "Check for undocumented error scenarios"
- "Validate all links and cross-references"
- "Ensure examples use realistic data"
- "Verify accessibility of images and diagrams"

### Emergency Review Template

**No time for full review? Use this:**

```markdown
## Rapid Doc Review

### Critical Checks
- [ ] Version matches current release
- [ ] No broken/incorrect procedures
- [ ] Security-sensitive info accurate
- [ ] No obvious inaccuracies

### Quick Scan
- [ ] TOC covers all major topics
- [ ] Screenshots appear current
- [ ] Contact/support info present

### Verdict: ✅ / ⚠️ / ❌

### If Issues Found:
- [List critical issues only]
```

---

## 🌟 Final Thoughts

> **"Documentation is a love letter that you write to your future self and your users."**

User guide review is not just about finding errors - it is about:
- **Empowering Users** - Enabling them to succeed without support
- **Reducing Friction** - Making the product easier to use
- **Building Trust** - Accurate docs build confidence in the product
- **Enabling Scale** - Good documentation scales support

**Remember:**
- ✅ Users read documentation when they are stuck - help them get unstuck
- ✅ Every ambiguity costs user time and support tickets
- ✅ Outdated docs are worse than no docs
- ✅ Review is an act of user advocacy

---

## 📚 Related Skills

- **Test Case Review** - For validating test coverage
- **Prompt Enhancement** - For crafting better review prompts
- **Requirements Analysis** - For understanding feature scope

---

*Last Updated: 2024*  
*Version: 1.0 - Comprehensive Edition*

**Happy Documenting! 📖✨**
