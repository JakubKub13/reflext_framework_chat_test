"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from reflex_test import ui


def about_us() -> rx.Component:
    #  About Us Page
    return ui.base_layout(
        rx.vstack(
            rx.heading("Welcome to About us!", size="9"),
            rx.link(
                rx.button("Check out our docs!"),
                href="https://reflex.dev/docs/getting-started/introduction/",
                is_external=True,
            ),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
        rx.logo(),
    )
    


