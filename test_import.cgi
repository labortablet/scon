#!/usr/bin/env python3
import scon_actions
import cgitb
cgitb.enable()


print("Content-Type: text/html\n\n")
b = getattr(scon_actions, "test")(a=1)
print("<html><body><p>No Error Happened")
print(b)
print("</p></body></html>")
