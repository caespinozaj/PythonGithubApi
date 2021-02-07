from github import Github

# initialize API
gh = Github()

# create repository 'test' in github and set local directory to 'test-local'.
repo = gh.create_repository("test-1", directory="test-local")

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
