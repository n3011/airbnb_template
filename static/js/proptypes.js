//proptypes
var proptype_arr = new Array("Apartment", "House", "Bed & Breakfast", "Loft", "Townhouse", "Condominium", "Bungalow", "Cabin", "Villa", "Castle", "Dorm", "Threehouse", "Boat", "Plane", "Camper/RV", "lgloo", "Lighthouse", "Yurt", "Tipi", "Cave", "Island", "Chalet", "Earth House", "Hut", "Train", "Tent", "Other");

function populateProptypes(proptypeElementId) {
    // given the id of the <select> tag as function argument, it inserts <option> tags
    var proptypeElement = document.getElementById(proptypeElementId);
    proptypeElement.length = 0;
    proptypeElement.options[0] = new Option('Select Property', '-1');
    proptypeElement.selectedIndex = 0;
    for (var i = 0; i < proptype_arr.length; i++) {
        proptypeElement.options[proptypeElement.length] = new Option(proptype_arr[i], proptype_arr[i]);
    }
}
