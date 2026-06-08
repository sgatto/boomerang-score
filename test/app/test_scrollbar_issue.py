"""
Regression test for a UI bug where multiple scrollbars were accumulating in the ParticipantTableView.
This test ensures that rebuilding the table view does not leak widgets (specifically scrollbars)
in the parent frame.
"""

import tkinter as tk
from tkinter import ttk
import pytest
import os
from boomerang_score.app.components.table_view import ParticipantTableView
from boomerang_score.core.models import Competition
from boomerang_score.core import ACC, AUS

@pytest.mark.skipif(os.environ.get('DISPLAY') is None, reason="No display available")
def test_scrollbar_accumulation():
    """
    Verifies that calling build() multiple times on ParticipantTableView 
    clears previous widgets and doesn't accumulate scrollbars.
    
    The bug occurred because the scrollbar was being created as a child of the 
    parent frame but wasn't explicitly destroyed during a rebuild, leading to 
    multiple scrollbars appearing when toggling disciplines.
    """
    root = tk.Tk()
    root.withdraw()
    
    disciplines = [ACC, AUS]
    disc_state = {
        ACC.code: tk.BooleanVar(value=True),
        AUS.code: tk.BooleanVar(value=True)
    }
    competition = Competition()
    service = None
    fonts = {"bold": "Helvetica 10 bold", "main": "Helvetica 10"}
    
    view = ParticipantTableView(root, disciplines, disc_state, competition, service, fonts)
    
    # First build
    view.build()
    initial_children = view.frame.winfo_children()
    initial_count = len(initial_children)
    
    # Second build
    view.build()
    after_second_build_children = view.frame.winfo_children()
    after_second_count = len(after_second_build_children)
    
    # If the bug exists, after_second_count will be > initial_count
    # because a new scrollbar is added each time.
    try:
        assert after_second_count == initial_count, f"Expected {initial_count} children, but got {after_second_count}. Children: {after_second_build_children}"
    finally:
        root.destroy()

if __name__ == "__main__":
    # Manually run if needed
    try:
        test_scrollbar_accumulation()
        print("Test passed!")
    except Exception as e:
        print(f"Test failed: {e}")
