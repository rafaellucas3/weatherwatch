from dataclasses import dataclass

@dataclass
class Location:
    '''
    A class to represent a location. If the location services more than one business i.e. Ottawa Spoke, it should be entered twice (once per each business unit).
    ...
    Attributes
    ----------
    retailerSiteId: str
        The OSP identifier for a location.
    name: str
        The complete name of the location.
    acronym: str
        The acronym of the location.
    region: str
        The region which this location is linked to.
    business: str
        The type of business this location is operating to (Home Delivery, In Store Fullfilment, etc.)
    kind: str
        The kind of this location.
    address: str
        The complete address of the location.
    geo_coordinates: str
        The geographic coordinates of the location.
    
    Methods
    ----------
    plot: Returns a folium map with a marker pointing to the geo_coordinates.

    '''
    retailerSiteID: str
    retailOutletLocationSk : int
    name: str
    acronym: str
    region : str
    business : str
    kind: str
    address: str
    geo_coordinates: tuple
