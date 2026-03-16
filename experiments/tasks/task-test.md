Analyze the SQL macro files in this codebase and produce a summary report.

Your goal:
1. Find all SQL macro definition files
2. For each file, count: number of macros defined, whether they return TABLE or scalar values
3. List any macros that call other macros (dependencies)

Write your findings to a file called `macro-audit.md` in the root of the workspace.

The file should contain:
- A table with columns: File, Macro Name, Return Type (TABLE/SCALAR), Dependencies
- A total count of macros at the bottom

Success criteria:
- macro-audit.md exists and contains the analysis
- All macro files were found and analyzed
- Return types are correctly classified
- Dependencies are identified where they exist
