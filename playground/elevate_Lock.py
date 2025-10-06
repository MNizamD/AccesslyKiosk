# testCMD_wexpect.py
import wexpect
user = "Administrator"
child = wexpect.spawn(f'runas /user:{user} "dist\\NizamLab\\Main.exe"')

child.expect(f'password for {user}: ')   # exact prompt text may vary
child.sendline('iamadmin')
child.sendline('exit')
print(child.before)
child.terminate()