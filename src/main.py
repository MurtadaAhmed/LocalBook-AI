import flet as ft
import database
import os
import ingestion
import threading

def main(page: ft.Page):
    page.title = "LocalBook AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.session.set("active_notebook_id", None)

    # --- CHAT UI LOGIC ---#
    chat_list = ft.ListView(expand=True, spacing=20, auto_scroll=True)

    def create_chat_bubble(role: str, content: str):
        is_user = role == "user"
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(content, color=ft.colors.WHITE if is_user else ft.colors.BLACK),
                    bgcolor=ft.colors.BLUE_700 if is_user else ft.colors.GREY_300,
                    padding=15,
                    border_radius=10,
                    width=600
                )
            ],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        )

    def load_chat_history(notebook_id):
        chat_list.controls.clear()
        messages = database.get_messages_by_notebook(notebook_id)

        if not messages:
            chat_list.controls.append(
                ft.Text("No messages yet. Ask a question about your documents!", color=ft.colors.GREY_500, text_align=ft.TextAlign.CENTER)
            )
        else:
            for msg in messages:
                role = msg[0]
                content = msg[1]
                chat_list.controls.append(create_chat_bubble(role, content))
        page.update()


    # --- FILE DASHBOARD LOGIC --

    files_row = ft.Row(wrap=True)

    def load_workspace_files(notebook_id):
        files_row.controls.clear()
        files = ingestion.get_notebook_files(notebook_id)

        def delete_file_handler(e, file_path_to_delete):
            ingestion.delete_document_from_notebook(notebook_id, file_path_to_delete)
            load_workspace_files(notebook_id)

        if files:
            for f in files:
                file_name = os.path.basename(f)
                files_row.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.INSERT_DRIVE_FILE, size=14, color=ft.colors.WHITE70),
                            ft.Text(file_name, size=12, color=ft.colors.WHITE),
                            ft.IconButton(
                                icon=ft.icons.CLOSE,
                                icon_color=ft.colors.RED_300,
                                icon_size=14,
                                tooltip="Remove file from workspace",
                                on_click=lambda e, fp=f: delete_file_handler(e, fp)
                            )
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor=ft.colors.BLUE_GREY_800,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=15
                    )
                )
        page.update()

    # --- SIDEBAR UI LOGIC ---#
    notebook_list = ft.ListView(expand=True, spacing=5)

    def delete_notebook_handler(notebook_id):
        database.delete_notebook(notebook_id)
        ingestion.clear_notebook_vector_store(notebook_id)

        if page.session.get("active_notebook_id") == notebook_id:
            page.session.set("active_notebook_id", None)
            chat_list.controls.clear()
            files_row.controls.clear()
            chat_list.controls.append(
                ft.Text("Please select or create a workspace from the left menu.", color=ft.colors.GREY_500, text_align=ft.TextAlign.CENTER)
            )
        load_notebooks()

    def load_notebooks():
        notebook_list.controls.clear()
        all_notebooks = database.get_all_notebooks()

        active_id = page.session.get("active_notebook_id")

        for nb in all_notebooks:
            nb_id = nb[0]
            nb_name = nb[1]
            is_active = (nb_id == active_id)
            del_btn = ft.IconButton(
                icon=ft.icons.DELETE,
                icon_color=ft.colors.RED_400,
                tooltip="Delete Workspace",
                on_click=lambda e, id=nb_id: delete_notebook_handler(id)
            )

            notebook_list.controls.append(
                ft.ListTile(
                    title=ft.Text(nb_name, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL),
                    leading=ft.Icon(ft.icons.LIBRARY_BOOKS, color=ft.colors.BLUE_400 if is_active else None),
                    trailing=del_btn,
                    selected=is_active,
                    bgcolor=ft.colors.BLUE_GREY_800 if is_active else None,
                    on_click=lambda e, id=nb_id: select_notebook(id)
                )
            )
        page.update()

    def select_notebook(notebook_id):
        page.session.set("active_notebook_id", notebook_id)
        load_chat_history(notebook_id)
        load_workspace_files(notebook_id)

        load_notebooks()

    # --- Dialog Logic ---

    new_notebook_field = None

    def add_notebook(e):
        if new_notebook_field.value:
            database.create_notebook(new_notebook_field.value)
            new_notebook_field.value = ""
            load_notebooks()
            page.dialog.open = False
            page.update()

    new_notebook_field = ft.TextField(
        label="Notebook Name",
        autofocus=True,
        on_submit=add_notebook
    )

    new_notebook_dialog = ft.AlertDialog(
        title=ft.Text("Create New Workspace"),
        content=new_notebook_field,
        actions=[ft.TextButton("Create", on_click=add_notebook)]
    )

    def open_new_notebook_dialog(e):
        page.dialog = new_notebook_dialog
        new_notebook_dialog.open = True
        page.update()

    # --- FILE UPLOAD LOGIC ---

    def handle_file_upload(e: ft.FilePickerResultEvent):
        active_id = page.session.get("active_notebook_id")
        if not active_id or not e.files:
            return

        file_path = e.files[0].path

        chat_list.controls.append(
            ft.Text(f"processing {e.files[0].name} ... please wait.", color=ft.colors.YELLOW_400, italic=True)
        )
        page.update()

        ingestion.add_document_to_notebook(active_id, file_path)
        chat_list.controls.pop()
        load_workspace_files(active_id)

    file_picker = ft.FilePicker(on_result=handle_file_upload)
    page.overlay.append(file_picker)



    # --- INPUT BAR LOGIC ---

    user_input = None

    def handle_send_click(e):
        active_id = page.session.get("active_notebook_id")

        if not active_id or not user_input.value:
            return

        user_text = user_input.value
        user_input.value = ""

        database.save_message(active_id, "user", user_text)
        chat_list.controls.append(create_chat_bubble("user", user_text))
        ai_bubble = create_chat_bubble("ai", "")
        chat_list.controls.append(ai_bubble)
        page.update()

        history_db = database.get_messages_by_notebook(active_id)
        chat_history_formatted = []
        temp_user_msg = ""
        for msg in history_db:
            role = msg[0]
            content = msg[1]
            if role == "user":
                temp_user_msg = content
            elif role == "ai":
                # Only append complete pairs.
                # (This naturally ignores the new user question we just saved above)
                if temp_user_msg and content:
                    chat_history_formatted.append((temp_user_msg, content))
                    temp_user_msg = ""
        chat_history_formatted = chat_history_formatted[-3:]
        def stream_ai_response():
            import brain
            full_response = ""
            for chunk in brain.ask_question_stream(active_id, user_text, chat_history_formatted):
                if chunk["type"] == "token":
                    full_response += chunk["content"]
                    ai_bubble.controls[0].content.value = full_response
                    chat_list.scroll_to(offset=-1, duration=0)
                    page.update()
                elif chunk["type"] == "sources":
                    database.save_message(active_id, "ai", full_response)

        threading.Thread(target=stream_ai_response, daemon=True).start()


    user_input = ft.TextField(
        hint_text="As a question about your documents",
        expand=True,
        border_radius=20,
        filled=True,
        shift_enter=True,
        on_submit=handle_send_click
    )



    upload_button = ft.IconButton(
        icon = ft.icons.ATTACH_FILE,
        icon_color=ft.colors.GREY_400,
        icon_size=25,
        on_click=lambda _: file_picker.pick_files(allow_multiple=False)
    )

    send_button = ft.IconButton(
        icon = ft.icons.SEND_ROUNDED,
        icon_color=ft.colors.BLUE_400,
        icon_size=30,
        on_click=handle_send_click
    )

    input_row = ft.Row(
        controls=[upload_button, user_input, send_button],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # --- LAYOUT CONSTRUCTION ---

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
        padding=20,
        content=ft.Column(
            controls=[
                files_row,
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                chat_list,
                input_row
            ]
        )
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

    chat_list.controls.append(
        ft.Text("Please select or create a workspace from the left menu.", color=ft.colors.GREY_500, text_align=ft.TextAlign.CENTER))
    page.update()

if __name__ == "__main__":
    ft.app(target=main)