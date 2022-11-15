# simple.py
from pylint.lint import Run

Run(['./src/lambdas/modify_cloudtrail'], do_exit=False)