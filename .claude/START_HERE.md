# Start New Thread - Quick Reference

## 📋 Copy & Paste This Into New Claude Code Threads

```
Read and follow .claude/NEW_THREAD_PROMPT.md - this contains all protocols and context for MockExamify.

Key points:
- MUST follow testing protocol (.claude_testing_protocol.md)
- MUST follow development workflows (CLAUDE_WORKFLOW.md)
- MUST use TodoWrite for complex tasks
- MUST run tests before completing tasks
- NEVER complete with failing tests

Now proceed with my request below.

---

[YOUR REQUEST GOES HERE]
```

---

## 🎯 That's It!

Just copy the text above, paste it into a new Claude Code conversation, and add your request at the bottom.

Claude will automatically:
1. Read the handoff prompt
2. Follow all testing protocols
3. Use proper workflows
4. Create todo lists
5. Run comprehensive tests
6. Report results clearly

---

## 📚 Documentation Structure

```
.claude/
├── START_HERE.md              ← You are here (quick reference)
├── NEW_THREAD_PROMPT.md       ← Complete handoff for new threads
└── context_prompt.md          ← Detailed project context

Root directory:
├── .claude_testing_protocol.md ← Testing rules (CRITICAL)
├── CLAUDE_WORKFLOW.md          ← Development workflows (CRITICAL)
├── README.md                   ← Project overview
└── run_tests.py                ← Test runner
```

---

## 💡 Pro Tips

### For Quick Bug Fixes
```
Read .claude/NEW_THREAD_PROMPT.md

Quick bug fix needed - follow Bug Fix Workflow.

Issue: [describe bug]
```

### For New Features
```
Read .claude/NEW_THREAD_PROMPT.md

New feature request - follow Feature Addition Workflow.

Feature: [describe feature]
```

### For Refactoring
```
Read .claude/NEW_THREAD_PROMPT.md

Refactoring task - follow Refactoring Workflow.

Goal: [describe refactoring]
```

---

**That's all you need! Just reference .claude/NEW_THREAD_PROMPT.md and Claude has full context.**
