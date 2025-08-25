from nicegui import ui, app
from app.auth_service import AuthService
from app.models import UserCreate, UserLogin
from typing import Optional


class AuthUI:
    """UI components for authentication"""

    @staticmethod
    def create_login_page():
        """Create the login page"""

        @ui.page("/login")
        def login_page():
            # Apply modern theme
            ui.colors(
                primary="#2563eb",
                secondary="#64748b",
                accent="#10b981",
                positive="#10b981",
                negative="#ef4444",
                warning="#f59e0b",
                info="#3b82f6",
            )

            with ui.column().classes("items-center justify-center min-h-screen bg-gray-50"):
                with ui.card().classes("w-96 p-8 shadow-xl rounded-xl bg-white"):
                    ui.label("🤧 Sneeze Tracker").classes("text-3xl font-bold text-center mb-2 text-gray-800")
                    ui.label("Sign in to your account").classes("text-center text-gray-600 mb-6")

                    username_input = ui.input("Username").classes("w-full mb-4").props("outlined")
                    password_input = ui.input("Password", password=True).classes("w-full mb-4").props("outlined")

                    error_label = ui.label("").classes("text-red-500 text-sm mb-4").style("display: none")

                    async def handle_login():
                        if not username_input.value or not password_input.value:
                            error_label.set_text("Please enter both username and password")
                            error_label.style("display: block")
                            return

                        try:
                            login_data = UserLogin(username=username_input.value, password=password_input.value)

                            user = AuthService.authenticate_user(login_data)
                            if user is None:
                                error_label.set_text("Invalid username or password")
                                error_label.style("display: block")
                                return

                            # Store user in session
                            app.storage.user["user_id"] = user.id
                            app.storage.user["username"] = user.username

                            ui.navigate.to("/dashboard")
                            ui.notify("Welcome back!", type="positive")

                        except Exception:
                            error_label.set_text("An error occurred during login")
                            error_label.style("display: block")

                    ui.button("Sign In", on_click=handle_login).classes(
                        "w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 rounded-lg mb-4"
                    )

                    with ui.row().classes("justify-center"):
                        ui.label("Don't have an account?").classes("text-gray-600")
                        ui.link("Sign up", "/register").classes("text-blue-500 hover:text-blue-600 ml-1 font-medium")

    @staticmethod
    def create_register_page():
        """Create the registration page"""

        @ui.page("/register")
        def register_page():
            ui.colors(
                primary="#2563eb",
                secondary="#64748b",
                accent="#10b981",
                positive="#10b981",
                negative="#ef4444",
                warning="#f59e0b",
                info="#3b82f6",
            )

            with ui.column().classes("items-center justify-center min-h-screen bg-gray-50"):
                with ui.card().classes("w-96 p-8 shadow-xl rounded-xl bg-white"):
                    ui.label("🤧 Create Account").classes("text-3xl font-bold text-center mb-2 text-gray-800")
                    ui.label("Join the sneeze tracking community").classes("text-center text-gray-600 mb-6")

                    username_input = ui.input("Username").classes("w-full mb-4").props("outlined")
                    email_input = ui.input("Email").classes("w-full mb-4").props("outlined")
                    password_input = ui.input("Password", password=True).classes("w-full mb-4").props("outlined")
                    confirm_password_input = (
                        ui.input("Confirm Password", password=True).classes("w-full mb-4").props("outlined")
                    )

                    error_label = ui.label("").classes("text-red-500 text-sm mb-4").style("display: none")

                    async def handle_register():
                        # Validation
                        if not all(
                            [
                                username_input.value,
                                email_input.value,
                                password_input.value,
                                confirm_password_input.value,
                            ]
                        ):
                            error_label.set_text("Please fill in all fields")
                            error_label.style("display: block")
                            return

                        if password_input.value != confirm_password_input.value:
                            error_label.set_text("Passwords do not match")
                            error_label.style("display: block")
                            return

                        if len(password_input.value) < 8:
                            error_label.set_text("Password must be at least 8 characters")
                            error_label.style("display: block")
                            return

                        try:
                            user_data = UserCreate(
                                username=username_input.value, email=email_input.value, password=password_input.value
                            )

                            user = AuthService.register_user(user_data)
                            if user is None:
                                error_label.set_text("Username or email already exists")
                                error_label.style("display: block")
                                return

                            # Auto-login after registration
                            app.storage.user["user_id"] = user.id
                            app.storage.user["username"] = user.username

                            ui.navigate.to("/dashboard")
                            ui.notify("Account created successfully! Welcome!", type="positive")

                        except Exception:
                            error_label.set_text("An error occurred during registration")
                            error_label.style("display: block")

                    ui.button("Create Account", on_click=handle_register).classes(
                        "w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 rounded-lg mb-4"
                    )

                    with ui.row().classes("justify-center"):
                        ui.label("Already have an account?").classes("text-gray-600")
                        ui.link("Sign in", "/login").classes("text-blue-500 hover:text-blue-600 ml-1 font-medium")

    @staticmethod
    def require_auth() -> Optional[int]:
        """Check if user is authenticated, redirect to login if not. Returns user_id if authenticated."""
        user_id = app.storage.user.get("user_id")
        if user_id is None:
            ui.navigate.to("/login")
            return None
        return user_id

    @staticmethod
    def logout():
        """Log out the current user"""
        app.storage.user.clear()
        ui.navigate.to("/login")
        ui.notify("You have been logged out", type="info")
