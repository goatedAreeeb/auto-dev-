import os

os.chdir("d:/hackathon")

print("Adding files...")
os.system("git add .")

print("Committing...")
os.system("git commit -m \"chore: align tests and schemas with strict (0, 1) reward constraints\"")

print("Pushing to origin...")
os.system("git push origin main")

print("Pushing to huggingface...")
os.system("git push hf main")

print("Done!")
