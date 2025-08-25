from nicegui import ui, app
from app.auth_ui import AuthUI
from app.sneeze_service import SneezeService
from app.models import SeverityLevel, SneezeCreate
import logging

logger = logging.getLogger(__name__)


class DashboardUI:
    """UI components for the main dashboard"""

    @staticmethod
    def get_severity_color(severity: SeverityLevel) -> str:
        """Get color for severity level"""
        color_map = {
            SeverityLevel.LIGHT: "#10b981",  # green
            SeverityLevel.MODERATE: "#f59e0b",  # amber
            SeverityLevel.HEAVY: "#ef4444",  # red
            SeverityLevel.EXPLOSIVE: "#7c2d12",  # dark red
        }
        return color_map.get(severity, "#64748b")

    @staticmethod
    def get_severity_icon(severity: SeverityLevel) -> str:
        """Get emoji icon for severity level"""
        icon_map = {
            SeverityLevel.LIGHT: "👃",
            SeverityLevel.MODERATE: "🤧",
            SeverityLevel.HEAVY: "💥",
            SeverityLevel.EXPLOSIVE: "🌋",
        }
        return icon_map.get(severity, "👃")

    @staticmethod
    def create_dashboard():
        """Create the main dashboard page"""

        @ui.page("/dashboard")
        def dashboard_page():
            user_id = AuthUI.require_auth()
            if user_id is None:
                return

            ui.colors(
                primary="#2563eb",
                secondary="#64748b",
                accent="#10b981",
                positive="#10b981",
                negative="#ef4444",
                warning="#f59e0b",
                info="#3b82f6",
            )

            # Header
            with ui.row().classes("w-full justify-between items-center p-4 bg-white shadow-sm mb-6"):
                ui.label("🤧 Sneeze Tracker").classes("text-2xl font-bold text-gray-800")

                with ui.row().classes("items-center gap-4"):
                    username = app.storage.user.get("username", "User")
                    ui.label(f"Welcome, {username}!").classes("text-gray-600")
                    ui.button("Logout", on_click=AuthUI.logout).classes("bg-gray-500 text-white px-4 py-2 rounded")

            with ui.column().classes("max-w-6xl mx-auto px-4"):
                # Stats cards
                stats_container = ui.row().classes("gap-4 w-full mb-6")
                DashboardUI.create_stats_section(user_id, stats_container)

                # Action buttons
                with ui.row().classes("gap-4 mb-6"):
                    ui.button("Add New Sneeze", on_click=lambda: ui.navigate.to("/add-sneeze")).classes(
                        "bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-lg"
                    )
                    ui.button("View All Sneezes", on_click=lambda: ui.navigate.to("/sneezes")).classes(
                        "bg-green-500 hover:bg-green-600 text-white font-semibold px-6 py-3 rounded-lg"
                    )

                # Recent sneezes
                ui.label("Recent Sneezes").classes("text-xl font-bold text-gray-800 mb-4")
                sneezes_container = ui.column().classes("w-full")
                DashboardUI.display_recent_sneezes(user_id, sneezes_container)

    @staticmethod
    def create_stats_section(user_id: int, container):
        """Create the stats cards section"""
        with container:
            container.clear()

            stats = SneezeService.get_sneeze_stats(user_id)

            # Total sneezes card
            with ui.card().classes("p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow"):
                ui.label("Total Sneezes").classes("text-sm text-gray-500 uppercase tracking-wider")
                ui.label(str(stats["total_count"])).classes("text-3xl font-bold text-gray-800 mt-2")

            # Today's sneezes card
            with ui.card().classes("p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow"):
                ui.label("Today").classes("text-sm text-gray-500 uppercase tracking-wider")
                ui.label(str(stats["today_count"])).classes("text-3xl font-bold text-blue-600 mt-2")

            # This month card
            with ui.card().classes("p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow"):
                ui.label("This Month").classes("text-sm text-gray-500 uppercase tracking-wider")
                ui.label(str(stats["this_month_count"])).classes("text-3xl font-bold text-green-600 mt-2")

            # Severity breakdown
            with ui.card().classes("p-6 bg-white shadow-lg rounded-xl hover:shadow-xl transition-shadow"):
                ui.label("Severity Breakdown").classes("text-sm text-gray-500 uppercase tracking-wider mb-3")
                for severity, count in stats["severity_counts"].items():
                    if count > 0:
                        with ui.row().classes("items-center gap-2 mb-1"):
                            ui.label(DashboardUI.get_severity_icon(severity)).classes("text-lg")
                            ui.label(f"{severity.value.title()}: {count}").classes("text-sm text-gray-700")

    @staticmethod
    def display_recent_sneezes(user_id: int, container):
        """Display recent sneezes in a container"""
        with container:
            container.clear()

            recent_sneezes = SneezeService.get_user_sneezes(user_id, limit=5)

            if not recent_sneezes:
                ui.label("No sneezes recorded yet. Add your first sneeze!").classes("text-gray-500 text-center p-8")
                return

            for sneeze in recent_sneezes:
                with ui.card().classes("p-4 bg-white shadow-md rounded-lg mb-3"):
                    with ui.row().classes("items-center justify-between w-full"):
                        with ui.row().classes("items-center gap-3"):
                            ui.label(DashboardUI.get_severity_icon(sneeze.severity)).classes("text-2xl")
                            with ui.column().classes("gap-1"):
                                ui.label(f"{sneeze.severity.value.title()} Sneeze").classes(
                                    "font-semibold text-gray-800"
                                )
                                ui.label(sneeze.timestamp.strftime("%Y-%m-%d %H:%M")).classes("text-sm text-gray-500")
                                if sneeze.notes:
                                    ui.label(sneeze.notes).classes("text-sm text-gray-600 italic")

                        # Colored indicator
                        ui.label("●").style(
                            f"color: {DashboardUI.get_severity_color(sneeze.severity)}; font-size: 1.5rem"
                        )

    @staticmethod
    def create_add_sneeze_page():
        """Create the add sneeze page"""

        @ui.page("/add-sneeze")
        def add_sneeze_page():
            user_id = AuthUI.require_auth()
            if user_id is None:
                return

            ui.colors(
                primary="#2563eb",
                secondary="#64748b",
                accent="#10b981",
                positive="#10b981",
                negative="#ef4444",
                warning="#f59e0b",
                info="#3b82f6",
            )

            with ui.column().classes("max-w-2xl mx-auto p-6"):
                # Header with back button
                with ui.row().classes("items-center gap-4 mb-6"):
                    ui.button("← Back to Dashboard", on_click=lambda: ui.navigate.to("/dashboard")).classes(
                        "bg-gray-500 text-white px-4 py-2 rounded"
                    )
                    ui.label("Add New Sneeze").classes("text-2xl font-bold text-gray-800")

                with ui.card().classes("w-full p-8 shadow-xl rounded-xl bg-white"):
                    ui.label("Record Your Sneeze").classes("text-xl font-semibold mb-6 text-center text-gray-800")

                    # Severity selection
                    ui.label("Severity Level").classes("text-sm font-medium text-gray-700 mb-2")
                    severity_select = (
                        ui.select(
                            options={
                                SeverityLevel.LIGHT: f"{DashboardUI.get_severity_icon(SeverityLevel.LIGHT)} Light",
                                SeverityLevel.MODERATE: f"{DashboardUI.get_severity_icon(SeverityLevel.MODERATE)} Moderate",
                                SeverityLevel.HEAVY: f"{DashboardUI.get_severity_icon(SeverityLevel.HEAVY)} Heavy",
                                SeverityLevel.EXPLOSIVE: f"{DashboardUI.get_severity_icon(SeverityLevel.EXPLOSIVE)} Explosive",
                            },
                            value=SeverityLevel.MODERATE,
                        )
                        .classes("w-full mb-4")
                        .props("outlined")
                    )

                    # Notes
                    ui.label("Notes (Optional)").classes("text-sm font-medium text-gray-700 mb-2")
                    notes_input = ui.textarea("Describe your sneeze...").classes("w-full mb-6").props("outlined rows=3")

                    error_label = ui.label("").classes("text-red-500 text-sm mb-4").style("display: none")

                    async def handle_add_sneeze():
                        try:
                            if severity_select.value is None:
                                error_label.set_text("Please select a severity level")
                                error_label.style("display: block")
                                return

                            sneeze_data = SneezeCreate(severity=severity_select.value, notes=notes_input.value or "")

                            sneeze = SneezeService.create_sneeze(user_id, sneeze_data)
                            if sneeze is None:
                                error_label.set_text("Failed to record sneeze")
                                error_label.style("display: block")
                                return

                            ui.notify("Sneeze recorded successfully!", type="positive")
                            ui.navigate.to("/dashboard")

                        except Exception as e:
                            logger.error(f"Error recording sneeze: {str(e)}")
                            error_label.set_text("An error occurred while recording the sneeze")
                            error_label.style("display: block")

                    with ui.row().classes("gap-4 justify-center"):
                        ui.button("Cancel", on_click=lambda: ui.navigate.to("/dashboard")).classes(
                            "bg-gray-500 text-white px-6 py-3 rounded-lg"
                        )
                        ui.button("Record Sneeze", on_click=handle_add_sneeze).classes(
                            "bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg"
                        )
