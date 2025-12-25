# Issue #5936: `animate_opacity` not working

from flet import AnimationCurve, Page, Container, Button, Row, Column, Slider, Text, Animation
import flet as ft


def main(page: Page):
    page.title = "Flet Animation Demo"

    box = Container(width=120, height=120, bgcolor="#2196F3", border_radius=8, opacity=1.0)

    def animate(duration=500, curve=AnimationCurve.EASE_IN_OUT):
        box.animate = Animation(duration, curve)
        page.update()

    def toggle_size(e):
        if box.width == 120:
            box.width, box.height = 220, 220
        else:
            box.width, box.height = 120, 120
        animate(500)

    def toggle_opacity(e):
        box.opacity = 0.2 if box.opacity == 1 else 1
        animate(1000)

    def toggle_color(e):
        box.bgcolor = "#e91e63" if box.bgcolor == "#2196F3" else "#2196F3"
        animate(600)

    def on_scale_change(e):
        v = e.control.value  # 0.0 .. 1.0
        size = int(80 + 240 * v)
        box.width = box.height = size
        animate(200, AnimationCurve.LINEAR)

    controls = Column(
        [
            Row([Text("Animated box:"), box], alignment=ft.MainAxisAlignment.START),
            Row(
                [
                    Button("Toggle size", on_click=toggle_size),
                    Button("Toggle opacity", on_click=toggle_opacity),
                    Button("Toggle color", on_click=toggle_color),
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            ),
            Text("Scale (slider):"),
            Slider(min=0, max=1, divisions=20, value=0.175, on_change=on_scale_change),
        ],
        tight=True,
    )

    page.add(controls)

if __name__ == "__main__":
    ft.run(main=main)