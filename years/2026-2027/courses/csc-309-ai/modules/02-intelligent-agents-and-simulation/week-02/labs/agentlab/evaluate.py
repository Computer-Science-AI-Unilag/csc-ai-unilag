"""Batch evaluation entry point. The main guard is required for Windows workers."""
from agentlab.evaluation import main

if __name__=='__main__':
    raise SystemExit(main())
