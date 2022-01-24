# Elo ranking for English Premier League teams
Website that parses match results since 1992-1993 season and calculates elo rating for each EPL team
## How it works

The Elo rating system is a method for calculating the relative skill levels of players in zero-sum games such as chess. It is named after its creator Arpad Elo, a Hungarian-American physics professor.

This website implements the same approach to the English Premiere League clubs. It does not consider such factors as home team advantage. Ratings of the English teams take into account all official matches starting from the season 1992-1993. Relegation-promotion issue is managed by setting relegated team to the 1200 rating and setting promoted team to the 1500 rating.

Basic Elo formula:

Rn = Ro + P

Where:

Rn – new rating

Ro – old rating

P – change of rating

Change of rating is calculated by this formula:

P = K*G*(W-We)

Where:

K – tournament constant (website uses 40 for EPL)

G – goal difference constant

W – match result

We – expected match result


Expected match result is calculated by this formula:

We = 1 / (10^(-dr/400)+1)

Where:

dr – rating difference.
