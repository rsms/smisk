# encoding: utf-8

'''
GET /handler?x=2&y=A
'''

'''
POST /handler
Content-Type: application/x-www-form-urlencoded

x=2&y=A
'''

'''
POST /handler&x=2
Content-Type: application/x-www-form-urlencoded

y=A
'''

'''
POST /handler&x=2
Content-Type: application/json

{"y":"A"}
'''

# Resultat
{'x': 2, 'y': 'A'}
