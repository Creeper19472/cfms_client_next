from typing import TYPE_CHECKING
import gettext
import flet as ft
import include.ui.constants as const
from include.ui.controls.filemanager import FileManagerView
from include.ui.util.file_controls import get_directory

if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class HomeNavigationBar(ft.NavigationBar):
    def __init__(self, parent_view: "HomeModel", views: list[ft.Control] = []):
        self.parent_view = parent_view

        self.last_selected_index = 2  # 默认值设置成初次进入时默认选中的页面在效果上较好
        self.views = views

        nav_destinations = [
            ft.NavigationBarDestination(icon=ft.Icons.FOLDER, label="Files"),
            ft.NavigationBarDestination(icon=ft.Icons.ARROW_CIRCLE_DOWN, label="Tasks"),
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.MORE_HORIZ, label="More"),
        ]

        super().__init__(
            nav_destinations,
            selected_index=2,
            on_change=self.on_change_item,
            # visible=False
        )

    async def on_change_item(self, e: ft.Event[ft.NavigationBar]):
        for view in self.views:
            if self.views.index(view) == e.control.selected_index:
                view.visible = True
            else:
                view.visible = False
        yield

        if e.control.selected_index == 0:
            assert type(self.views[0]) == FileManagerView
            await get_directory(
                self.views[0].current_directory_id, self.views[0].file_listview
            )

        # control: MyNavBar = e.control
        # match control.selected_index:
        #     case 0:  # Files
        #         files_container.visible = True
        #         home_container.visible = False
        #         settings_container.visible = False
        #         load_directory(self.page, folder_id=current_directory_id)

        #     case 1:
        #         control.selected_index = control.last_selected_index
        #         self.page.go("/home/tasks#object_type=document")
        #     case 2:
        #         files_container.visible = False
        #         home_container.visible = True
        #         settings_container.visible = False
        #         self.page.update()
        #     case 3:
        #         files_container.visible = False
        #         home_container.visible = False
        #         settings_container.visible = True
        #         settings_avatar.content = ft.Text(
        #             self.page.session.store.get("username")[0].upper()
        #         )
        #         _nickname = self.page.session.store.get("nickname")
        #         settings_username_display.value = (
        #             _nickname if _nickname else self.page.session.store.get("username")
        #         )
        #         self.page.update()
        #     case 4:
        #         control.selected_index = control.last_selected_index
        #         _refresh_user_list_function: function = self.page.session.store.get(
        #             "refresh_user_list"
        #         )
        #         _refresh_user_list_function(e.page, _update_page=False)
        #         self.page.go("/home/manage")
        #     # case 4:
        #     #     self.page.go("/logos")
        #     # case 5:
        #     #     self.page.go("/slides")
        # control.last_selected_index = control.selected_index


class WelcomeInfoCard(ft.Card):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ACCESS_TIME_FILLED),
                        title=ft.Text(_("欢迎访问 保密文档管理系统（CFMS）")),
                        subtitle=ft.Text(_("落霞与孤鹜齐飞，秋水共长天一色。")),
                    ),
                ]
            ),
            # width=400,
            padding=10,
        )


class HomeTabs(ft.Tabs):
    def __init__(
        self,
        ref: ft.Ref | None = None,
    ):
        self.tabbar_ref = ft.Ref[ft.TabBar]()
        self.tabbarview_ref = ft.Ref[ft.TabBarView]()

        _tabbar = ft.TabBar(
            tabs=[
                ft.Tab(label=_("收藏")),
            ],
            ref=self.tabbar_ref,  # pyright: ignore[reportArgumentType]
        )
        _tabbarview = ft.TabBarView(
            expand=True,
            controls=[
                ft.Container(
                    ft.Column(
                        controls=[ft.Text("您尚未收藏任何文档或文件夹。")],
                        # alignment=ft.alignment.center,
                    ),
                    margin=15,
                ),
            ],
            ref=self.tabbarview_ref,  # pyright: ignore[reportArgumentType]
        )

        super().__init__(
            selected_index=0,
            length=1,
            expand=True,
            content=ft.Column(controls=[_tabbar, _tabbarview], expand=True),
            ref=ref,
        )


class HomeView(ft.Container):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)

        self.margin = 10
        self.padding = 10

        self.content = ft.Column(
            controls=[
                WelcomeInfoCard(),
                HomeTabs(),
            ]
        )

        # Form variable definitions

        # Form reference definitions

        # Form element definitions
