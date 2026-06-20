import flet as ft
import database
import os
import ingestion
import threading
import settings
import psutil
import time

def main(page: ft.Page):
    page.title = "LocalBook AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.session.set("active_notebook_id", None)

    # --- RESOURCE MONITOR UI ---
    cpu_text = ft.Text("CPU: 0%", color=ft.colors.WHITE70, size=12)
    ram_text = ft.Text("RAM: 0%", color=ft.colors.WHITE70, size=12)
    page.appbar = ft.AppBar(
        title=ft.Text("LocalBook AI", size=16, weight=ft.FontWeight.BOLD),
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.Row([
                ft.Icon(ft.icons.MEMORY, size=16, color=ft.colors.BLUE_400),
                cpu_text,
                ft.Container(width=10),
                ft.Icon(ft.icons.STORAGE, size=16, color=ft.colors.BLUE_400),
                ram_text,
                ft.Container(width=20)  # right margin padding
            ], alignment=ft.MainAxisAlignment.CENTER)
        ]
    )

    def update_system_stats():
        psutil.cpu_percent(interval=None)
        while True:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent

                cpu_text.value = f"CPU: {cpu:.1f}%"
                ram_text.value = f"RAM: {ram:.1f}%"

                # Turn text red if hardware is struggling!
                cpu_text.color = ft.colors.RED_400 if cpu > 85 else ft.colors.WHITE70
                ram_text.color = ft.colors.RED_400 if ram > 85 else ft.colors.WHITE70

                page.update()
                time.sleep(1.5)  # Refresh rate
            except Exception:
                break

    threading.Thread(target=update_system_stats, daemon=True).start()
    def preload_ai_models():
        import brain
        import ingestion
        print("Background Thread: Warming up AI models...")
        ingestion.get_embedding_model()
        brain.get_llm()
        print("Background Thread: AI models are fully loaded and ready!")

    threading.Thread(target=preload_ai_models, daemon=True).start()


    # --- CHAT UI LOGIC ---#
    chat_list = ft.ListView(expand=True, spacing=20, auto_scroll=True)

    def create_chat_bubble(role: str, content):
        is_user = role == "user"
        if isinstance(content, str):
            display_content = ft.Text(content, color=ft.colors.WHITE if is_user else ft.colors.BLACK)
        else:
            display_content = content
        return ft.Row(
            controls=[
                ft.Container(
                    content=display_content,
                    bgcolor=ft.colors.BLUE_700 if is_user else ft.colors.GREY_300,
                    padding=15,
                    border_radius=10,
                    width=600
                )
            ],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        )

    def load_chat_history(notebook_id):

        messages = database.get_messages_by_notebook(notebook_id)
        chat_list.controls.clear()
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

        files = ingestion.get_notebook_files(notebook_id)
        files_row.controls.clear()

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
        load_notebooks()
        load_chat_history(notebook_id)
        load_workspace_files(notebook_id)



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
        loading_view = ft.Row([
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.colors.BLACK),
            ft.Text("Thinking...", color=ft.colors.BLACK, italic=True)
        ])
        ai_bubble = create_chat_bubble("ai", loading_view)
        chat_list.controls.append(ai_bubble)
        page.update()
        from ingestion import get_notebook_files
        files = get_notebook_files(active_id)
        if not files:
            ai_bubble.controls[0].content = ft.Text(
                "⚠️ This workspace has no documents. Please upload a file first.",
                color=ft.colors.ORANGE_400
            )
            page.update()
            return
        history_db = database.get_recent_messages_by_notebook(active_id, limit=4)
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
        chat_history_formatted = chat_history_formatted
        def stream_ai_response():
            import brain
            full_response = ""
            is_first_token = True
            for chunk in brain.ask_question_stream(active_id, user_text, chat_history_formatted):
                if chunk["type"] == "token":
                    if is_first_token:
                        ai_bubble.controls[0].content = ft.Text("", color=ft.colors.BLACK)
                        is_first_token = False
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



    current_cfg = settings.load_settings()

    def on_temp_change(e):
        temp_slider.label = f"Temperature: {temp_slider.value:.1f}"
        page.update()

    def on_penalty_change(e):
        penalty_slider.label = f"Repetition Penalty: {penalty_slider.value:.2f}"
        page.update()

    initial_temp = current_cfg.get("temperature", 0.3)
    temp_slider = ft.Slider(
        min=0.1, max=1.0, divisions=9,
        value=initial_temp,
        label=f"Temperature: {initial_temp:.1f}",
        on_change=on_temp_change
    )
    initial_penalty = current_cfg.get("repeat_penalty", 1.15)
    penalty_slider = ft.Slider(
        min=1.0, max=1.5, divisions=10,
        value=initial_penalty,
        label=f"Repetition Penalty: {initial_penalty:.2f}",
        on_change=on_penalty_change
    )

    tokens_input = ft.TextField(
        label="Max Generation Tokens",
        value=str(current_cfg.get("max_tokens", 4096)),
        width=200
    )

    prompt_input = ft.TextField(
        label="Default System Prompt Persona",
        value=current_cfg.get("system_prompt", ""),
        multiline=True,
        min_lines=4,
        max_lines=10,
        height=150
    )

    def save_settings_click(e):
        try:
            new_cfg = {
                "temperature": float(temp_slider.value),
                "repeat_penalty": float(penalty_slider.value),
                "max_tokens": int(tokens_input.value),
                "system_prompt": prompt_input.value
            }
            if settings.save_settings(new_cfg):
                import brain
                brain.update_llm_settings_live()
                page.snack_bar = ft.SnackBar(ft.Text("Settings saved and AI model successfully hot-swapped"), bgcolor=ft.colors.GREEN_700)
                page.snack_bar.open = True
                page.update()
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error parsing inputs: {err}"), bgcolor=ft.colors.RED_700)
            page.snack_bar.open = True
            page.update()

    settings_view = ft.Container(
        padding=30,
        expand=True,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=25,
            controls=[
                ft.Text("Application & Local AI Model Tuning", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(color=ft.colors.OUTLINE),

                ft.Text("Model Creativity (Temperature)", weight=ft.FontWeight.BOLD),
                ft.Text("Lower values are factual and predictable, higher values are creative.", size=12, color=ft.colors.GREY_400),
                temp_slider,

                ft.Text("Repetition Control (Repeat Penalty)", weight=ft.FontWeight.BOLD),
                ft.Text("Prevents the model from falling into loops or repeating sentences.", size=12, color=ft.colors.GREY_400),
                penalty_slider,

                ft.Text("Response Bounds", weight=ft.FontWeight.BOLD),
                tokens_input,

                ft.Text("System Prompt Persona", weight=ft.FontWeight.BOLD),
                prompt_input,

                ft.ElevatedButton(
                    text="Save Configurations",
                    icon=ft.icons.SAVE,
                    bgcolor=ft.colors.BLUE_700,
                    color=ft.colors.WHITE,
                    on_click=save_settings_click,
                    height=45
                )
            ]
        )
    )

    tabs_container = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        expand=True,
        tabs=[
            ft.Tab(text="Workspace Chat", icon=ft.icons.CHAT_BUBBLE_OUTLINE, content=main_content),
            ft.Tab(text="Model Settings", icon=ft.icons.SETTINGS_OUTLINED, content=settings_view),
        ]
    )

    page.controls.clear()
    page.add(
        ft.Row(
            controls=[
                sidebar,
                ft.VerticalDivider(width=1, color=ft.colors.OUTLINE),
                tabs_container
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