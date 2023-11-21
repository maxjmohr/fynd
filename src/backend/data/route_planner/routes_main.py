from route import Route

# TODO: incorporate flight fetcher
# TODO: complete route selection algorithm (based on distance, time, price, etc.)

def main():

    # read key from text file
    with open("./../../../../res/auth/here_key.txt", "r") as f:
        key = f.read()

    # set some sample origins and destinations
    origin = (53.55166446, 10.003833318) # Hamburg
    # destinations are: Siegen, Tübingen, Reykjavik, Kiev, Naples
    destinations = [(50.883331, 8.016667), (48.521637, 9.057645), (64.13548, -21.89541), (50.4501, 30.5234), (40.8522, 14.2681)]
    date = "2023-11-22"

    # create route objects
    routes = [Route(origin, dest, date) for dest in destinations]

    # get the public transit routes
    public_transit_routes = [route.getPublicTransitRoute(key) for route in routes]

    # get the driving routes
    driving_routes = [route.getDrivingRoute(key) for route in routes]

    # get nearest aiports
    airport_path = "./../../../../res/master_data/airports.csv"
    nearest_airports = [route.getNearestAirport(airport_path) for route in routes]

    # get driving and transit route maps
    public_transit_maps = [route.plotRoute(transit_directions) for route, transit_directions in zip(routes, public_transit_routes)]
    driving_maps = [route.plotRoute(transit_directions) for route, transit_directions in zip(routes, public_transit_routes)]

    public_transit_maps[4].show_in_browser()


if __name__ == "__main__":
    main()