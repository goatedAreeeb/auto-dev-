import os

os.chdir("d:/hackathon")

print("Adding files...")
os.system("git add .")

print("Committing...")
os.system("git commit -m \"Critical Fix: Apply bounding rules and formatted validation output log directly to root inference.py evaluated by the Phase 2 validator\"")

print("Pushing to origin...")
os.system("git push origin main")

print("Pushing to huggingface...")
os.system("git push hf main")

print("Done!")
