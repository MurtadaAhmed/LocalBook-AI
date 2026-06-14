import flet as ft
import database

def main(page: ft.Page):
    page.title = "LocalBook AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.session.set("active_notebook_id", None)

    notebook_list = ft.ListView(expand=True, spacing=5)

    def load_notebooks():
        notebook_list.controls.clear()
        all_notebooks = database.get_all_notebooks()

        for nb in all_notebooks:
            nb_id = nb[0]
            nb_name = nb[1]

            notebook_list.controls.append(
                ft.ListTile(
                    title=ft.Text(nb_name),
                    leading=ft.Icon(ft.icons.LIBRARY_BOOKS),
                    on_click=lambda e, id=nb_id: select_notebook(id)
                )
            )
        page.update()

    def select_notebook(notebook_id):
        page.session.set("active_notebook_id", notebook_id)
        print(f"User selected Notebook ID: {notebook_id}")

    new_notebook_field = ft.TextField(label="Notebook Name", autofocus=True)

    def add_notebook(e):
        if new_notebook_field.value:
            database.create_notebook(new_notebook_field.value)
            new_notebook_field.value = ""
            load_notebooks()
            page.dialog.open = False
            page.update()

    new_notebook_dialog = ft.AlertDialog(
        title=ft.Text("Create New Workspace"),
        content=new_notebook_field,
        actions=[ft.TextButton("Create", on_click=add_notebook)]
    )

    def open_new_notebook_dialog(e):
        page.dialog = new_notebook_dialog
        new_notebook_dialog.open = True
        page.update()

    sidebar = ft.Container(
        width=260,
        bgcolor=ft.colors.SURFACE_VARIANT,
        padding=10,
        content=ft.Column(
            controls=[
                ft.Text("Workspaces", size=20, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton(" + New Notebook", on_click=open_new_notebook_dialog, width=240),
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

    load_notebooks()

if __name__ == "__main__":
    ft.app(target=main)