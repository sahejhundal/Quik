import webapp2
import os
import jinja2
import hmac
import time
import datetime
import operator
from PIL import Image

hashcode=""

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import images

#template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)), autoescape=True)

def hash_str(s):
    return hmac.new(hashcode, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    val=h.split('|')[0]
    if h==make_secure_val(val):
        return val

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


def isLoggedIn(s):
    if s==None or s=="None":
        return False
    else:
        return True

def xHoursAgo(x):
    fmt = '%a %b %d %H:%M:%S +0000 %Y'
    time.strftime(fmt)
    createdat = x
    createdtim = time.strptime(createdat, fmt)
    hoursago = (time.time() - time.mktime(createdtim)) / 3600
    return int(hoursago)

def timesince(x):
    y=x
    fmt = '%a %b %d %H:%M:%S +0000 %Y'
    time.strftime(fmt)
    createdat = x.strftime(fmt)
    createdtim = time.strptime(createdat, fmt)
    secsago = (time.time() - time.mktime(createdtim))
    minsago = (time.time() - time.mktime(createdtim)) / 60
    hoursago = (time.time() - time.mktime(createdtim)) / 3600
    daysago = (time.time() - time.mktime(createdtim)) / (3600*24)
    weeksago = (time.time() - time.mktime(createdtim)) / (3600*24*7)
    if minsago < 1:
        return "%ds ago" % int(int(secsago)+1)
    elif hoursago < 1:
        return "%dm ago" % int(int(minsago))
    elif hoursago >=1 and hoursago < 24:
        return "%dh ago" % int(int(hoursago))
    elif hoursago >= 24 and daysago < 2:
        return "Yesterday"
    elif daysago >= 2 and daysago < 7:
        return y.strftime("%A")
    elif daysago >= 7:
        return y.strftime("%b %-d")
    else:
        return "Couldn't calculate the time"
    return int(hoursago)


#----------------------------------------

class custFunc(webapp2.RequestHandler):
    def main(self, the_file, needchats=None, **params):
        user_cookie_str = self.request.cookies.get("user")
        user=0
        final_chats=[]
        if user_cookie_str:
            user_val=check_secure_val(user_cookie_str)
            if user_val:
                user=str(user_val)
                u=Users.by_user(user)
                if u:
                    if needchats:
                        chats=Chat.query().fetch(10)
                        print "\nGot chats\n"
                        return self.render(the_file, chats=chats, u=u, **params)
                    return self.render(the_file, **params)
                else:
                    self.response.headers.add_header('Set-Cookie', 'user=None; path=/')
                    return self.redirect("/signin")
            else:
                self.response.headers.add_header('Set-Cookie', 'user=None; path=/')
                return self.redirect("/")
        else:
            self.response.headers.add_header('Set-Cookie', 'user=None; path=/')
            return self.redirect("/")

class Handler(webapp2.RequestHandler):
    def write(self,*a, **kw):
        self.response.out.write(*a,**kw)
    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))
    def login(self, username, password):
        new_user_val=make_secure_val(str(username))
        self.response.headers.add_header('Set-Cookie','user=%s' % new_user_val)
    def delete(self, todelete, property, name):
        u=ndb.GqlQuery("SELECT * FROM %s WHERE %s='%s'" % (todelete, property, name))
        ndb.delete(u)
    def signout(self):
        self.response.headers.add_header('Set-Cookie', 'user=None; path=/')
        self.redirect("/")
    def verifyForms(self, type, var):
        valid_name='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '
        valid_username='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_.'
        valid_email='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_.@'
        valid_number='+0123456789'
        if type=="name":
            if len(var)<4:
                return None
            for i in var:
                if i not in valid_name:
                    return None
            return "Valid"
        if type=="username":
            if len(var)<=3:
                return None
            for i in var:
                if i not in valid_username:
                    return None
            return "Valid"
        if type=="email":
            for i in var:
                if i not in valid_email:
                    return None
            return "Valid"
        if type=="number":
            if len(var)!=10:
                return None
            for i in var:
                if i not in valid_number:
                    return None
            return "Valid"
        if type=='password':
            if len(var)<=7:
                return None
            return "Valid"
        else:
            return None

    def getLoginInfo(self):
        user_cookie_str = self.request.cookies.get("user")
        if user_cookie_str=="None" or user_cookie_str==None:
            return None
        if user_cookie_str:
            user_val=check_secure_val(user_cookie_str)
            if user_val:
                u=Users.by_user(user_val)
                if u:
                    return str(user_val)

class Chat(ndb.Model):
    started=ndb.DateTimeProperty(auto_now_add = True)
    to=ndb.StringProperty()
    me=ndb.StringProperty()
    toname=ndb.StringProperty()
    mename=ndb.StringProperty()
    lastmessage=ndb.TextProperty()
    lastmessagetime=ndb.DateTimeProperty()
    lastmessageby=ndb.StringProperty()
    readby=ndb.StringProperty()

    def render(self):
        return render_str("chat.html", c = self)

class Text(ndb.Model):
    content=ndb.TextProperty()
    author=ndb.StringProperty(required = True)
    seen=ndb.StringProperty()
    sent=ndb.StringProperty()
    created=ndb.DateTimeProperty(auto_now_add = True)

class imageText(ndb.Model):
    content=ndb.BlobProperty()
    author=ndb.StringProperty(required = True)
    created=ndb.DateTimeProperty(auto_now_add = True)

class postImage(webapp2.RequestHandler):
    def get(self, postid):
        print "Got it"
        key = ndb.Key.from_path('Post', int(postid), parent=blog_key())
        post = ndb.get(key)
        if post.image:
            self.response.headers['Content-Type'] = 'image/jpeg'
            self.response.out.write(post.image)
            return
        else:
            print "No image"
            self.response.out.write('No image')

class userImage(webapp2.RequestHandler):
    def get(self, username):
        print "Got it"
        user = Users.all().filter('username =', username).get()
        if user.photo:
            self.response.headers['Content-Type'] = 'image/jpeg'
            self.response.out.write(user.photo)
            return
        else:
            print "No image"
            self.response.out.write('No image')

class NewChat(Handler, custFunc):
    def get(self):
        response = self.getLoginInfo()
        if not response:
            self.render("signin.html", error="You need to login to create a post!")
        elif response:
            #custFunc.main(self,"newchat.html")
            self.render("newchat.html", username=response)

    def post(self):
        to=self.request.get("to")
        content=self.request.get("content")
        response = self.getLoginInfo()
        if response:
            if to and content:
                target=Users.by_user(to)
                user=Users.by_user(response)
                print "\n\n\n"
                print target
                if target:
                    content = content.replace('\n', '<br>')
                    a = Chat(to=str(to), me=str(response), lastmessage=str(content), lastmessagetime=datetime.datetime.now(),
                    lastmessageby=response, readby=response, toname=target.name, mename=user.name)
                    a.put()
                    b = Text(parent=a.key, content=content, author=response, sent=str(time.time()))
                    b.put()
                    return self.redirect("/")
                return self.render("newchat.html", error="There was no user by that username.")
            else:
                custFunc.main(self,"newchat.html",error="Please fill all of the boxes!")
        else:
            self.redirect('/signin')

class MainPage(Handler, custFunc):
    def get(self):
        response=self.getLoginInfo()
        if not response:
            self.signout()
            self.redirect('/signin')
        chats = Chat.query(ndb.OR(Chat.to == response,
                           Chat.me == response)).order(-Chat.lastmessagetime).fetch()
        final_chats=[]
        for i in chats:
            if response==i.me:
                i.other_person=i.to
            else:
                i.other_person=i.me
            i.xcreated=timesince(i.lastmessagetime)
            final_chats.append(i)
        self.render("index.html", chats=final_chats, username=response)

    def post(self):
        q=self.request.get("q")
        if q:
            posts=ndb.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
            final_posts=[]
            for i in posts:
                if q.upper() in (i.title).upper() or q.upper() in (i.content).upper() or q.upper() in (i.author).upper():
                    final_posts.append(i)
            if final_posts==[]:
                return self.main("index.html", error="No matching results for %s" % q,
                end="Results for %s" % q, search=q)
            return self.main("index.html", posts=final_posts, end="Results for %s" % q, search=q)
        return self.redirect('/')

class Google(Handler):
    def get(self):
        user=users.get_current_user()
        if user:
            self.render("register.html", username=user.user_id(), value_email=user.email())
        else:
            self.redirect(users.create_login_url(self.request.uri))


class Blog(Handler, custFunc):
    def get(self):
        response=self.getLoginInfo()
        if response:
            self.render('about.html', url2="/signout", text2="log-out",
                url1="/usr/%s" % response, text1="person", url3="/newpost", text3="edit")
        else:
            self.render('about.html')

class ChatPage(Handler, custFunc):
    def get(self, username):
        response=self.getLoginInfo()
        chat = Chat.query(ndb.AND(Chat.to == username,
                           Chat.me == response)).get()
        if not chat:
            chat = Chat.query(ndb.AND(Chat.to == response,
                               Chat.me == username)).get()
        if chat==None:
            return self.render("newchat.html", username=response, target=username)
        chats = Chat.query(ndb.OR(Chat.to == response,
                           Chat.me == response)).order(-Chat.lastmessagetime).fetch()
        messages=Text.query(ancestor=chat.key).order(-Text.created).fetch(20)
        messages.sort(key=lambda x: x.created)
        final_chats=[]
        for i in chats:
            if response==i.me:
                i.other_person=i.to
            else:
                i.other_person=i.me
            i.xcreated=timesince(i.lastmessagetime)
            final_chats.append(i)
        if chat.readby and chat.readby!=response:
            chat.readby="Both"
        chat.put()
        if response==chat.me:
            chat.other_person=chat.to
        else:
            chat.other_person=chat.me
        self.render('permalink.html', chats=chats, chat=chat, username=str(response), messages=messages)
    def post(self, username):
        text = self.request.get('text')
        chat_id = self.request.get('chat_id')
        if not text.isspace() and text!="":
            key = ndb.Key('Chat', int(chat_id))
            response = self.getLoginInfo()
            thechat = key.get()
            thechat.lastmessage=text
            thechat.lastmessagetime=datetime.datetime.now()
            thechat.lastmessageby=response
            thechat.readby=response
            thechat.put()
            if response:
                a = Text(parent=thechat.key, author=response, content=text, sent=str(time.time()))
                a.put()
                print "Put done!"
                #commenthtml='<div class="comment"><div class="post-comment-author"><a href="usr/%s">%s</a></div><div class="post-comment">%s</div></div>' % (response, response, comment)
                #ret="%s %s" % (post_id, commenthtml)
                #self.response.out.write(ret)
                #return self.redirect('/p/%s' % int(post_id))
                return self.redirect('/chat/%s' % username)
            else:
                self.render('permalink.html', post=post, error="Don't you think you should login first?")


class Users(ndb.Model):
    name=ndb.StringProperty()
    username=ndb.StringProperty(required = True)
    password=ndb.StringProperty(required = True)
    photo=ndb.BlobProperty()
    bio=ndb.TextProperty()
    email=ndb.StringProperty()
    number=ndb.StringProperty()
    registered=ndb.DateTimeProperty(auto_now_add = True)

    def trender(self):
        return render_str("user.html", u = self)

    @classmethod
    def by_user(cls, name):
        return Users.query().filter(Users.username == name).get()

class UserPage(Handler, custFunc):
    def get(self, user_id):
        #key = ndb.Key.from_path('Users', int(user_id))
        #user = ndb.get(key)
        tuser = Users.all().filter('username =', user_id).get()
        posts = ndb.GqlQuery("SELECT * FROM Post WHERE author = '%s' ORDER BY created DESC" % tuser.username)
        a=self.getLoginInfo()
        if not tuser:
            self.error(404)
            return
        final_posts=[]
        for i in posts:
            i.xcreated = timesince(i.created)
            final_posts.append(i)
        if posts:
            if a==tuser.username:
                return self.main("userlink.html", user = tuser, final_posts=final_posts, owner="True!")
            return self.main("userlink.html", user = tuser, final_posts=final_posts)
        if a==tuser.username:
            return self.main("userlink.html", user = tuser, owner="True!")
        return self.main("userlink.html", user = tuser)

class EditUser(Handler, custFunc):
    def get(self):
        response = self.getLoginInfo()
        if response:
            user = Users.all().filter('username =', response).get()
            self.main("edituser.html", user=user)
        else:
            return self.redirect('/')
    def post(self):
        response = self.getLoginInfo()
        if response:
            user =  Users.all().filter('username =', response).get()
            name = self.request.get("name")
            email = self.request.get("email")
            number = self.request.get("number")
            bio = self.request.get("bio")
            photo = self.request.POST.get("image", None)
            try:
                photo.value
                photo = images.resize(photo.value, 512,512)
                print "\n\n\nNew Photo found\n\n\n"
            except AttributeError:
                print "\n\n\nPhoto set to original photo\n\n\n"
                photo=user.photo
            if self.verifyForms('name', name)==None:
                return self.main("edituser.html", user=user,
                            error="Names only have alphabetical characters! ")
            if self.verifyForms('email', email)==None:
                return self.main("edituser.html", user=user,
                            error="Valid e-mail can contain only latin letters, numbers, '@' and '.' ")
            if self.verifyForms('number', number)==None:
                return self.main("edituser.html", user=user,
                            error="Numbers only have digits! ")
            if not None:
                user.name = name
                user.email = email
                user.number = number
                user.bio = bio
                user.website = website
                user.gender = gender
                user.photo = photo
                user.put()
                return self.main("edituser.html", user=user,
                            success="Changes were saved!")

class ChangePassword(Handler, custFunc):
    def get(self):
        response = self.getLoginInfo()
        if response:
            user = Users.all().filter('username =', response).get()
            self.main("changepassword.html",
                        username=user.username)
        else:
            return self.redirect('/signin')

    def post(self):
        response = self.getLoginInfo()
        if response:
            password = self.request.get("password")
            newpassword = self.request.get("newpassword")
            retypepassword = self.request.get("retypepassword")
            user =  Users.all().filter('username =', response).get()
            if password==user.password:
                if self.verifyForms(type='password', var=newpassword) != None:
                    if newpassword==retypepassword:
                        user.password=newpassword
                        user.put()
                        return self.main("changepassword.html", username=user.username, success="Changes were saved!")
                    else:
                        self.render("changepassword.html", username=user.username, error="Passwords do not match!")
                else:
                    self.render("changepassword.html", username=user.username, error="Password must be at least 8 characters!")
            else:
                self.render("changepassword.html", username=user.username, error="Password is not correct!")


class SignIn(Handler):
    def get(self):
        response=self.getLoginInfo()
        if response:
            self.render('signin.html', user=response)
        else:
            self.render('signin.html')
    def post(self):
        username=self.request.get("username")
        password=self.request.get("password")
        if username and password:
            u=Users.by_user(username)
            if u:
                if u.password==password:
                    self.login(username, password)
                    return self.redirect("/")
                else:
                    self.render("signin.html", error="Sorry, your password was incorrect", username=username)
            else:
                error="Sorry, your username was incorrect"
                self.render("signin.html", error=error)
        else:
            error="I couldn't connect to ThoughtsJournal"
            self.render("signin.html", error=error, username=username, password=password)

class SignUp(Handler):
    def get(self):
        response = self.getLoginInfo()
        if response:
            self.render('signin.html', user=response)
        else:
            self.render('signup.html')

    def post(self):
        username=self.request.get("username")
        number=self.request.get("number")
        password=self.request.get("password")
        name=self.request.get("name")
        u = Users.by_user(username)
        if username and password:
            isError = None
            error = ""
            if self.verifyForms(type='username', var=username) == None:
                isError = True
                error += 'The username is not valid!'
            if self.verifyForms(type='number', var=number) == None:
                isError = True
                error += 'The number is not valid!'
            if self.verifyForms(type='password', var=password) == None:
                isError = True
                error += 'The password does not qualify!'
            if isError:
                return self.render("signup.html", error=error, username=username, number=number,
                password=password)
            if u:
                error="You cannot use this username as it is already in use!"
                self.render("signup.html", error=error)
            else:
                s = Users(name=name, username = username, password = password, number = number,
                bio="I use ThoughtsJournal!")
                s.put()
                self.login(username, password)
                time.sleep(0.1)
                return self.redirect('/')
                #p=hash_str(password)
        else:
            return self.render("signup.html", errors='Please fill all the boxes',
                                   username=username, number=number, password=password)


class signout(Handler):
    def get(self):
        self.signout()


app = webapp2.WSGIApplication([
('/', MainPage),
('/newchat', NewChat),
('/signup', SignUp),
('/signout', signout),
('/signin', SignIn),
('/user/editme/general', EditUser),
('/user/editme/security', ChangePassword),
('/usr/([a-z0-9]+)', UserPage),
('/chat/([a-z0-9]+)', ChatPage),
('/p/img/([^/]+)', postImage),
('/usr/img/([a-z0-9]+)', userImage),
('/google', Google)],
 debug=True)
