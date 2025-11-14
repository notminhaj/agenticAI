## ISSUE: Added rank_results() tool but agent is not using it
- Upgraded tool description to show benefits of tool (still not using it)
- Updated task description prompt to add "Select only high quality papers that are most relevant"
- Still not using it

## NOTE: NN mode follows workflow mode style execution, no agent thinking involved
- The purpose of NN mode was to filter papers so only high quality papers are used for summarize()
- This saves token usage
- So why NN agent mode?
- To see if we can get better results, higher quality papers for the right costs
- This is better than summarizing each document and then deciding which ones are the best
- Agent also searches for more papers than manually requested.