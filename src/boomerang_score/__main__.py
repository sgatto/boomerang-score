"""Entry point of the package."""

# %% IMPORTS

from boomerang_score.app import ScoreTableApp

# %% MAIN

def main():
    app = ScoreTableApp()
    app.mainloop()

if __name__ == "__main__":
    main()
