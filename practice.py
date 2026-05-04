#name="nayab"
#for i in range(1000):
    #print(name)

name = ["nayab","ayesha"]
print(name)

temp=80
if temp==50:
    print("temparature is high")
elif temp>=60:
    print("temparature is too high")
else:
    print("temp is normal")

uname="nayab"
for i in uname:
    print(uname)

for i in uname:
    print(i,end=",")

for i in uname:
    print(i)


#age = int("twenty")     # program CRASHES here
#print(age) 

print("\n[ 1 ] No protection -- program crashes:")
try:
    age = int("twenty")
    print(f"  Age is {age}")
except Exception as e:
    print(f"  type:{type(e)}Error: {e}")
    print("  (Program stops here. Nothing below this would run.)")


name=["nayab","faryal"]
print(f"list of name is {name}")
a=14
b=15
print("addition is",a+b)