import json
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for


def loadClubs():
    with open("clubs.json") as c:
        listOfClubs = json.load(c)["clubs"]
        return listOfClubs


def loadCompetitions():
    with open("competitions.json") as comps:
        liste = json.load(comps)["competitions"]
        pastcompetitions = []
        listOfCompetitions = []
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for competition in liste:
            if competition["date"] < today:
                competition["past"] = True
                pastcompetitions.append(competition)
            else:
                competition["past"] = False
                listOfCompetitions.append(competition)
            print(competition)
        for comp in pastcompetitions:
            listOfCompetitions.append(comp)
        return listOfCompetitions


def save_clubs(clubs):
    with open("clubs.json", "w") as f:
        json.dump({"clubs": clubs}, f, indent=4)


def save_competitions(competitions):
    with open("competitions.json", "w") as f:
        json.dump({"competitions": competitions}, f, indent=4)


app = Flask(__name__)
app.secret_key = "something_special"

competitions = loadCompetitions()
clubs = loadClubs()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/welcome", methods=["POST", "GET"])
def welcome():
    email = (
        request.args.get("email")
        if request.method == "GET"
        else request.form.get("email")
    )

    clubs = loadClubs()
    competitions = loadCompetitions()

    club = [club for club in clubs if club["email"] == email]
    if not club:
        flash("Email non autorisé !")
        return redirect(url_for("index"))
    print("club : ", club[0]["name"])
    return render_template("welcome.html", club=club, competitions=competitions)


@app.route("/book/<competition>/<club>")
def book(competition, club):
    foundClub = [c for c in clubs if c["name"] == club]
    foundCompetition = [c for c in competitions if c["name"] == competition][0]
    if foundClub and foundCompetition:
        return render_template(
            "booking.html", club=foundClub, competition=foundCompetition
        )
    else:
        flash("Something went wrong-please try again")
        return render_template("welcome.html", club=club, competitions=competitions)


@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():

    club_name = request.form.get("club")
    print(club_name)
    competition_name = request.form.get("competition")
    print(competition_name)
    places_requested = int(request.form.get("places"))
    print(places_requested)

    clubs = loadClubs()
    competitions = loadCompetitions()

    competition = [c for c in competitions if c["name"] == request.form["competition"]]
    club = [c for c in clubs if c["name"] == request.form["club"]]
    placesRequired = int(places_requested)
    comp_place = competition[0]["numberOfPlaces"]
    competition[0]["numberOfPlaces"] = (
        int(competition[0]["numberOfPlaces"]) - placesRequired
    )
    if places_requested > competition[0]["numberOfPlaces"]:
        flash(
            f"Pas assez de plcs : demandé({places_requested}) > dispo({comp_place}) !"
        )
    elif places_requested > int(club[0]["points"]):
        flash(
            f"Pas assez de pts({club[0]['points']}) pour les {places_requested} plcs !"
        )
    else:
        # Mettre à jour les données
        competition[0]["numberOfPlaces"] = str(
            competition[0]["numberOfPlaces"] - places_requested
        )
        club[0]["points"] = str(int(club[0]["points"]) - places_requested)

        save_clubs(clubs)
        save_competitions(competitions)

        flash(
            f"Réservation réussie ! {places_requested} place(s) à {competition_name}."
        )
    return redirect(url_for("welcome", email=club[0]["email"]))


# TODO: Add route for points display


@app.route("/logout")
def logout():
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
