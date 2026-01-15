from django.test import TestCase, Client, override_settings
from django.urls import reverse
from casino.login.models import User


class LoginPageTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.url = reverse("login_page")
    
    def test_get_login_page(self):
        """Test GET request renders login page"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "casino/login/index.html")
    
    def test_authenticated_user_redirects_to_home(self):
        """Test authenticated users are redirected to home"""
        user = User.objects.create_user(username="testuser", password="testpass") # nosec
        self.client.force_login(user)  # Changed from login()
        
        response = self.client.get(self.url)
        
        self.assertRedirects(response, "/")
    
    def test_empty_pin(self):
        """Test empty PIN returns error"""
        response = self.client.post(self.url, {"pin": ""})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["register_err"], "Empty PIN")
    
    def test_wrong_pin(self):
        """Test wrong PIN returns error"""
        response = self.client.post(self.url, {"pin": "123456"})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["register_err"], "Wrong PIN")
    
    def test_correct_pin_sets_session_and_redirects(self):
        """Test correct PIN sets session and redirects to register"""
        response = self.client.post(self.url, {"pin": "213721372137"})
        
        self.assertRedirects(response, reverse("register"))
        self.assertTrue(self.client.session.get("legit"))
        self.assertIsNone(self.client.session.get("login_err"))
        self.assertIsNone(self.client.session.get("register_err"))
    
    def test_legit_session_flag_set_to_false_on_get(self):
        """Test that legit flag is set to False on GET"""
        self.client.get(self.url)
        
        self.assertFalse(self.client.session.get("legit"))


class LoginUserTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.url = reverse("login")
        # Correct way to create user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        ) # nosec
    
    def test_successful_login(self):
        """Test successful login redirects to home"""
        response = self.client.post(self.url, {
            "username": "testuser",
            "password": "testpass123"
        }) # nosec
        
        self.assertRedirects(response, "/")
        self.assertIsNone(self.client.session.get("login_err"))
        
        # Verify user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_successful_login_with_next_parameter(self):
        """Test login redirects to 'next' parameter if provided"""
        response = self.client.post(
            self.url + "?next=/coinflip/",
            {
                "username": "testuser",
                "password": "testpass123"
            }
        ) # nosec
        
        self.assertRedirects(response, "/coinflip/")
    
    def test_login_with_empty_next_parameter(self):
        """Test login with empty 'next' redirects to home"""
        response = self.client.post(
            self.url + "?next=",
            {
                "username": "testuser",
                "password": "testpass123"
            }
        ) # nosec
        
        self.assertRedirects(response, "/")
    
    def test_invalid_username(self):
        """Test login with invalid username"""
        response = self.client.post(self.url, {
            "username": "wronguser",
            "password": "testpass123"
        }) # nosec
        
        self.assertRedirects(response, reverse("login_page"))
        self.assertEqual(
            self.client.session.get("login_err"),
            "Invalid username and/or password."
        )
    
    def test_invalid_password(self):
        """Test login with invalid password"""
        response = self.client.post(self.url, {
            "username": "testuser",
            "password": "wrongpass"
        })
        
        self.assertRedirects(response, reverse("login_page"))
        self.assertEqual(
            self.client.session.get("login_err"),
            "Invalid username and/or password."
        )


class RegisterUserTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.url = reverse("register")
    
    def test_register_without_legit_session_redirects(self):
        """Test accessing register without PIN redirects to login"""
        response = self.client.get(self.url)
        
        self.assertRedirects(response, reverse("login_page"))
    
    def test_get_register_page_with_legit_session(self):
        """Test GET register page with valid session"""
        session = self.client.session
        session["legit"] = True
        session.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "casino/login/register.html")
    
    def test_password_mismatch(self):
        """Test registration with mismatched passwords"""
        session = self.client.session
        session["legit"] = True
        session.save()
        
        response = self.client.post(self.url, {
            "username": "newuser",
            "password": "password123",
            "password_rep": "password456"
        })
        
        self.assertRedirects(response, reverse("register"))
        self.assertEqual(
            self.client.session.get("login_err"),
            "passwords don't match"
        )
        self.assertFalse(User.objects.filter(username="newuser").exists())
    
    def test_empty_username(self):
        """Test registration with empty username"""
        session = self.client.session
        session["legit"] = True
        session.save()
        
        response = self.client.post(self.url, {
            "username": "",
            "password": "password123",
            "password_rep": "password123"
        })
        
        self.assertRedirects(response, reverse("register"))
        self.assertEqual(
            self.client.session.get("login_err"),
            "passwords don't match"
        )
    
    def test_empty_password(self):
        """Test registration with empty password"""
        session = self.client.session
        session["legit"] = True
        session.save()
        
        response = self.client.post(self.url, {
            "username": "newuser",
            "password": "",
            "password_rep": ""
        })
        
        self.assertRedirects(response, reverse("register"))
        self.assertEqual(
            self.client.session.get("login_err"),
            "passwords don't match"
        )
    
    def test_duplicate_username(self):
        """Test registration with existing username"""
        # Correct way to create user
        User.objects.create_user(username="existinguser", password="pass123") # nosec
        
        session = self.client.session
        session["legit"] = True
        session.save()
        
        response = self.client.post(self.url, {
            "username": "existinguser",
            "password": "newpass123",
            "password_rep": "newpass123"
        })
        
        self.assertRedirects(response, reverse("register"))
        self.assertEqual(
            self.client.session.get("login_err"),
            "user with this username already exists."
        )
    @override_settings(
        AUTH_PASSWORD_VALIDATORS=[
            {
                'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
                'OPTIONS': {'min_length': 10}
            },
            {
                'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
            },
        ]
    )
    def test_weak_password_too_short(self):
        """Test registration with password that's too short"""
        session = self.client.session
        session["legit"] = True
        session.save()
        
        response = self.client.post(self.url, {
            "username": "newuser",
            "password": "ab1",  # Too short (< 8 chars)
            "password_rep": "ab1"
        })
        
        self.assertRedirects(response, reverse("register"))
        login_err = self.client.session.get("login_err")
        self.assertIsNotNone(login_err)
        
        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username="newuser").exists())

    @override_settings(
        AUTH_PASSWORD_VALIDATORS=[
            {
                'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
            },
        ]
    )
    def test_weak_password_too_common(self):
        """Test registration with common password"""
        session = self.client.session
        session["legit"] = True
        session.save()
        
        response = self.client.post(self.url, {
            "username": "newuser",
            "password": "password123",  # Too common
            "password_rep": "password123"
        })
        
        self.assertRedirects(response, reverse("register"))
        login_err = self.client.session.get("login_err")
        self.assertIsNotNone(login_err)
        
        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username="newuser").exists())
    
    def test_successful_registration(self):
        """Test successful user registration"""
        session = self.client.session
        session["legit"] = True
        session.save()
        
        response = self.client.post(self.url, {
            "username": "newuser",
            "password": "SecurePassword123!",
            "password_rep": "SecurePassword123!"
        })
        
        self.assertRedirects(response, "/")
        
        # Verify user was created
        user = User.objects.get(username="newuser")
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password("SecurePassword123!"))
        
        # Verify user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "newuser")
        
        # Verify session cleared error
        self.assertIsNone(self.client.session.get("login_err"))
    
    def test_user_has_default_balance(self):
        """Test newly registered user has default balance"""
        session = self.client.session
        session["legit"] = True
        session.save()
        
        self.client.post(self.url, {
            "username": "newuser",
            "password": "SecurePassword123!",
            "password_rep": "SecurePassword123!"
        })
        
        user = User.objects.get(username="newuser")
        self.assertEqual(user.balance, 0)
        self.assertTrue(user.is_active)


class LogoutUserTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.url = reverse("logout")
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        ) # nosec
    
    def test_logout_redirects_to_login_page(self):
        """Test logout redirects to login page"""
        self.client.force_login(self.user)
        
        response = self.client.get(self.url)
        
        self.assertRedirects(response, reverse("login_page"))
    
    def test_logout_clears_authentication(self):
        """Test logout actually logs out the user"""
        self.client.force_login(self.user)
        
        # Verify user is logged in
        response = self.client.get(reverse("login_page"))
        self.assertRedirects(response, "/")  # Authenticated redirect
        
        # Logout
        self.client.get(self.url)
        
        # Verify user is logged out
        response = self.client.get(reverse("login_page"))
        self.assertEqual(response.status_code, 200)  # No redirect


class LoginFlowIntegrationTests(TestCase):
    """Test complete login flow from PIN to registration to login"""
    
    def setUp(self):
        self.client = Client()
    
    def test_complete_registration_flow(self):
        """Test complete flow: PIN -> Register -> Login"""
        # Step 1: Enter PIN
        response = self.client.post(
            reverse("login_page"),
            {"pin": "213721372137"}
        )
        self.assertRedirects(response, reverse("register"))
        
        # Step 2: Register
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password": "SecurePass123!",
                "password_rep": "SecurePass123!"
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Step 3: Logout
        self.client.get(reverse("logout"))
        
        # Step 4: Login with new credentials
        response = self.client.post(
            reverse("login"),
            {
                "username": "newuser",
                "password": "SecurePass123!"
            }
        )
        self.assertRedirects(response, "/")