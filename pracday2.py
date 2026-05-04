#user_comment = "This product is spam and totally spam."
#banned_words = "spam bad"
#print("Filtered comment:")
#for banned_word in banned_words.split():       # loop over each banned word
#    user_comment = user_comment.replace(banned_word, "****")  # .replace()
#print(f"  Result: {user_comment}")



#startswith
unames="nayab faryal"
for i in unames.split():
    if i.startswith("nayab"):
        print(f"{i}->sehar")
    elif i.startswith("faryal"):
        print(f"{i}->arshad")


#replace
name="nayab fatima"
repwords="fatima"
for i in repwords:
    name = name.replace(repwords,"sehar-")
print(f"result is:{name}")

#replace without loop
newname="nayab fatima"
newname=newname.replace("fatima","sehar")
print(newname)

 #while loop
name="nayab"
i=0
while i<3:
    print(name)
    i+=1

#upper()
name= "nayab sehar"
name=name.upper()
print(name)

#isdigit()
age="24"
age=age.isdigit()
print(age)

#endswith()
name="b a l"
if name.endswith("b"):
    print("nayab")
elif name.endswith("l"):
    print("faryal")
elif name.endswith("a"):
    print("ayesha")
else:
    print("nothing")

#break statement
name="nayab"
i=1
while i<=2:
    print(name)
    i+=1
    break

#continue statement
name="nayab sehar"
i=1
while i<=2:
    print(name)
    i+=1
    continue
    print("if continue used this will not work")

#pass
a=21
if a<15:
    print("yupp")
elif a<20:
    print("noo")
elif a>10:
    pass
    print("never")

#try/except
try:
    a="five"
    change=int(a)
except Exception as e:
    print("exception")

#exception as value-error
try:
    a="six"
    change=int(a)
except ValueError:
    print("value-error")

try:
    a="eight"
    change=int(a)
except ValueError as e:
    print(f"{e}")

#zero-division-error
a=10
b=0
try:
    c=a/b
    print(c)
except ZeroDivisionError:
    print("No. can't be divided by zero")

#attribute-error
a=None
try:
    change=a.lower()
    print(change)
except AttributeError:
    print("cannot perform on none type")

#type-error
try:
    add="five" + 25
except TypeError:
    print("cannot add string and integer")

#index-error
a="six"
try:
    print(a[5])
except IndexError:
    print("no index found")

#try/except/else/finally
a="25"
try:
    change=int(a)
except ValueError:
    print("error")
else:
    print("no error")
finally:
    print("done")

#list
a=["one","two","three"]
print(a)

#list with index
a=["one","two","three"]
print(a[2])

#list with slice
a=["one","two","three"]
print(a[:2])
