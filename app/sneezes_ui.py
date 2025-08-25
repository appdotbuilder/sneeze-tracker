from nicegui import ui
from datetime import date
from calendar import month_name
from app.auth_ui import AuthUI
from app.sneeze_service import SneezeService
from app.models import SeverityLevel


class SneezesUI:
    """UI components for viewing and managing sneezes"""

    @staticmethod
    def get_colored_nose_icon(severity: SeverityLevel) -> str:
        """Get colored nose emoji based on severity level"""
        icon_map = {
            SeverityLevel.LIGHT: "👃",  # Light green nose
            SeverityLevel.MODERATE: "🤧",  # Standard sneezing face
            SeverityLevel.HEAVY: "💥",  # Explosion for heavy
            SeverityLevel.EXPLOSIVE: "🌋",  # Volcano for explosive
        }
        return icon_map.get(severity, "👃")

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
    def create_sneezes_page():
        """Create the sneezes list page"""

        @ui.page("/sneezes")
        def sneezes_page():
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

            with ui.column().classes("max-w-6xl mx-auto p-6"):
                # Header
                with ui.row().classes("items-center gap-4 mb-6"):
                    ui.button("← Back to Dashboard", on_click=lambda: ui.navigate.to("/dashboard")).classes(
                        "bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
                    )
                    ui.label("Your Sneeze History").classes("text-2xl font-bold text-gray-800")

                # Filter controls
                filter_container = ui.row().classes("gap-4 mb-6 p-4 bg-white rounded-lg shadow-md")
                sneezes_container = ui.column().classes("w-full")

                SneezesUI.create_filters(user_id, filter_container, sneezes_container)
                SneezesUI.display_all_sneezes(user_id, sneezes_container)

    @staticmethod
    def create_filters(user_id: int, filter_container, sneezes_container):
        """Create filter controls"""
        current_date = date.today()

        with filter_container:
            ui.label("Filter by Month:").classes("text-sm font-medium text-gray-700 mb-2")

            with ui.row().classes("gap-3 items-end"):
                # Year selection
                current_year = current_date.year
                year_options = list(range(current_year - 2, current_year + 1))
                year_select = (
                    ui.select(options=year_options, value=current_year, label="Year")
                    .classes("w-24")
                    .props("outlined dense")
                )

                # Month selection
                month_options = {i: month_name[i] for i in range(1, 13)}
                month_select = (
                    ui.select(options=month_options, value=current_date.month, label="Month")
                    .classes("w-32")
                    .props("outlined dense")
                )

                # Filter button
                def apply_filter():
                    if year_select.value is not None and month_select.value is not None:
                        SneezesUI.display_filtered_sneezes(
                            user_id, year_select.value, month_select.value, sneezes_container
                        )

                ui.button("Filter", on_click=apply_filter).classes(
                    "bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition-colors"
                )

                # Show all button
                ui.button(
                    "Show All", on_click=lambda: SneezesUI.display_all_sneezes(user_id, sneezes_container)
                ).classes("bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded transition-colors")

    @staticmethod
    def display_all_sneezes(user_id: int, container):
        """Display all sneezes for the user"""
        with container:
            container.clear()

            sneezes = SneezeService.get_user_sneezes(user_id)

            if not sneezes:
                with ui.card().classes("p-8 text-center bg-white shadow-md rounded-lg"):
                    ui.label("🤧").classes("text-6xl mb-4")
                    ui.label("No sneezes recorded yet").classes("text-xl text-gray-600 mb-2")
                    ui.label("Start tracking your sneezes to see them here!").classes("text-gray-500")
                    ui.button("Add First Sneeze", on_click=lambda: ui.navigate.to("/add-sneeze")).classes(
                        "bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg mt-4 transition-colors"
                    )
                return

            SneezesUI.render_sneeze_list(sneezes, f"All Sneezes ({len(sneezes)} total)")

    @staticmethod
    def display_filtered_sneezes(user_id: int, year: int, month: int, container):
        """Display filtered sneezes for a specific month"""
        with container:
            container.clear()

            sneezes = SneezeService.get_sneezes_by_month(user_id, year, month)
            month_name_str = month_name[month]

            if not sneezes:
                with ui.card().classes("p-8 text-center bg-white shadow-md rounded-lg"):
                    ui.label("🤧").classes("text-4xl mb-4")
                    ui.label(f"No sneezes in {month_name_str} {year}").classes("text-xl text-gray-600 mb-2")
                    ui.label("Try a different month or add some sneezes!").classes("text-gray-500")
                    ui.button(
                        "Clear Filter", on_click=lambda: SneezesUI.display_all_sneezes(user_id, container)
                    ).classes("bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg mt-4 transition-colors")
                return

            SneezesUI.render_sneeze_list(sneezes, f"{month_name_str} {year} ({len(sneezes)} sneezes)")

    @staticmethod
    def render_sneeze_list(sneezes, title: str):
        """Render a list of sneezes with colored nose icons"""
        ui.label(title).classes("text-xl font-semibold text-gray-800 mb-4")

        # Group sneezes by date
        grouped_sneezes = {}
        for sneeze in sneezes:
            date_key = sneeze.timestamp.date()
            if date_key not in grouped_sneezes:
                grouped_sneezes[date_key] = []
            grouped_sneezes[date_key].append(sneeze)

        # Display grouped sneezes
        for date_key in sorted(grouped_sneezes.keys(), reverse=True):
            day_sneezes = grouped_sneezes[date_key]

            # Date header
            with ui.card().classes("mb-4 bg-gray-50 border border-gray-200"):
                with ui.card_section().classes("bg-gray-100 py-2"):
                    with ui.row().classes("items-center justify-between"):
                        ui.label(date_key.strftime("%A, %B %d, %Y")).classes("font-semibold text-gray-800")
                        ui.label(f"{len(day_sneezes)} sneeze{'s' if len(day_sneezes) != 1 else ''}").classes(
                            "text-sm text-gray-600 bg-gray-200 px-2 py-1 rounded"
                        )

                # Sneezes for this day
                with ui.card_section().classes("p-0"):
                    for i, sneeze in enumerate(day_sneezes):
                        border_class = "border-b border-gray-200" if i < len(day_sneezes) - 1 else ""

                        with ui.row().classes(
                            f"items-center justify-between p-4 hover:bg-gray-50 {border_class} transition-colors"
                        ):
                            with ui.row().classes("items-center gap-4"):
                                # Colored nose icon based on severity
                                with ui.column().classes("items-center gap-1"):
                                    # Main severity icon with color filter
                                    severity_color = SneezesUI.get_severity_color(sneeze.severity)
                                    nose_icon = SneezesUI.get_colored_nose_icon(sneeze.severity)

                                    # Display the icon with a colored background circle
                                    with (
                                        ui.element("div")
                                        .classes("w-12 h-12 rounded-full flex items-center justify-center")
                                        .style(
                                            f"background-color: {severity_color}20; border: 2px solid {severity_color}"
                                        )
                                    ):
                                        ui.label(nose_icon).classes("text-2xl")

                                    # Severity level indicator
                                    ui.label(sneeze.severity.value.title()).classes(
                                        "text-xs font-medium px-2 py-1 rounded-full text-white"
                                    ).style(f"background-color: {severity_color}")

                                # Sneeze details
                                with ui.column().classes("gap-1"):
                                    ui.label(sneeze.timestamp.strftime("%I:%M %p")).classes(
                                        "text-lg font-medium text-gray-800"
                                    )
                                    if sneeze.notes:
                                        ui.label(f'"{sneeze.notes}"').classes(
                                            "text-sm text-gray-600 italic max-w-md truncate"
                                        )

                            # Action buttons
                            with ui.row().classes("gap-2"):
                                if sneeze.notes:
                                    ui.button("📝", on_click=lambda s=sneeze: SneezesUI.show_sneeze_details(s)).classes(
                                        "p-2 text-blue-500 hover:bg-blue-50 rounded transition-colors"
                                    ).props("flat dense")

    @staticmethod
    def show_sneeze_details(sneeze):
        """Show detailed sneeze information in a dialog"""
        with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
            ui.label("Sneeze Details").classes("text-xl font-bold mb-4")

            with ui.column().classes("gap-4 w-full"):
                # Severity display with colored icon
                with ui.row().classes("items-center gap-4 p-3 bg-gray-50 rounded-lg"):
                    severity_color = SneezesUI.get_severity_color(sneeze.severity)
                    nose_icon = SneezesUI.get_colored_nose_icon(sneeze.severity)

                    # Colored icon circle
                    with (
                        ui.element("div")
                        .classes("w-16 h-16 rounded-full flex items-center justify-center")
                        .style(f"background-color: {severity_color}20; border: 3px solid {severity_color}")
                    ):
                        ui.label(nose_icon).classes("text-3xl")

                    with ui.column():
                        ui.label(f"{sneeze.severity.value.title()} Sneeze").classes("text-lg font-semibold")
                        ui.label("Severity Level").classes("text-sm text-gray-500")

                ui.separator()

                # Time information
                with ui.column().classes("gap-2"):
                    ui.label("Time:").classes("text-sm font-medium text-gray-700")
                    ui.label(sneeze.timestamp.strftime("%A, %B %d, %Y at %I:%M %p")).classes("text-gray-600")

                # Notes section
                with ui.column().classes("gap-2"):
                    ui.label("Notes:").classes("text-sm font-medium text-gray-700")
                    if sneeze.notes:
                        ui.label(sneeze.notes).classes(
                            "text-gray-600 bg-gray-50 p-3 rounded border-l-4 border-blue-200"
                        )
                    else:
                        ui.label("No notes recorded").classes("text-gray-500 italic")

                # Close button
                ui.button("Close", on_click=dialog.close).classes(
                    "bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded mt-4 transition-colors w-full"
                )

        dialog.open()
