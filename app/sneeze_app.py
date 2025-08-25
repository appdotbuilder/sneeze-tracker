from nicegui import ui
from app.auth_ui import AuthUI
from app.dashboard_ui import DashboardUI
from app.sneezes_ui import SneezesUI


def create():
    """Create and register all pages for the sneeze tracking application"""

    # Apply global theme
    ui.colors(
        primary="#2563eb",  # Professional blue
        secondary="#64748b",  # Subtle gray
        accent="#10b981",  # Success green
        positive="#10b981",
        negative="#ef4444",  # Error red
        warning="#f59e0b",  # Warning amber
        info="#3b82f6",  # Info blue
    )

    # Root redirect to dashboard (or login if not authenticated)
    @ui.page("/")
    def index():
        from nicegui import app

        user_id = app.storage.user.get("user_id")
        if user_id:
            ui.navigate.to("/dashboard")
        else:
            ui.navigate.to("/login")

    # Register authentication pages
    AuthUI.create_login_page()
    AuthUI.create_register_page()

    # Register main application pages
    DashboardUI.create_dashboard()
    DashboardUI.create_add_sneeze_page()
    SneezesUI.create_sneezes_page()
