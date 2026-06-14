import flet as ft
import database

def main(page: ft.Page):
    page.title = "LocalBook AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.session.set("active_notebook_id", None)
    page.add(ft.Text("Hello, GUI world", size=30))

    notebook_list = ft.ListView(expand=True, spacing=5)
    notebook_list.controls.append(ft.Text("notebooks will appear here ... ", color=ft.colors.GREEN_500))

    sidebar = ft.Container(
        width=260,
        bgcolor=ft.colors.SURFACE_VARIANT,
        padding=10,
        content=ft.Column(
            controls=[
                ft.Text("Workspaces", size=20, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton(" + New Notebook", width=240),
                ft.Divider(height=20, color=ft.colors.OUTLINE),
                notebook_list
            ]
        )
    )

    main_content = ft.Container(
        expand=True,
        padding=10,
        content=ft.Text("chat will go here")
    )

    page.add(
        ft.Row(
            controls=[
                sidebar,
                ft.VerticalDivider(width=1, color=ft.colors.OUTLINE),
                main_content
            ],
            expand=True,
            spacing=0
        )
    )

if __name__ == "__main__":
    ft.app(target=main)