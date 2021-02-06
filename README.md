# PythonGithubApi
API to use github CLI (gh) in python applications.
# Requirements
It is necessary to have github CLI installed and set up with your account for this to work.
# Usage
The only file you need in order to use the API is `github.py`. `example.py` provides an example use of the API, and `base` folder is used by this example.
```python
from github import Github

# initialize API
gh = Github()

# create repository 'test' in github and set local directory to 'test-local'.
repo = gh.create_repository("test", directory="test-local")

# copy all contents from "base" folder into my repository
repo.copy_root("base")

# add files, check status, commit and push.
repo.add("*")
print(repo.status())
repo.commit("added base files")
repo.push()

# create issue on said repository
issue = repo.create_issue(title="Can you create issues with this?",
                         body="Yes you can!")

# comment issue
issue.comment("Cool!")

# add collaborator to repository
repo.add_collaborator("your-collaborator-username-here")

# uncomment to delete local repository
# repo.delete()
```
# Notes
API will not work properly when initialized within a local repository. Please ensure `github.py` is not on the same directory as a `.git` directory.
