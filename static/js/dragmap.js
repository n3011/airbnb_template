<script src="https://maps.googleapis.com/maps/api/js?v=3.exp&signed_in=true&libraries=places"></script>
var geocoder;
var map;
var marker;

codeAddress = function () {
    geocoder = new google.maps.Geocoder();
  
  var address = document.getElementById('city_country').value;
  geocoder.geocode( { 'address': address}, function(results, status) {
    if (status == google.maps.GeocoderStatus.OK) {
      map = new google.maps.Map(document.getElementById('mapCanvas'), {
    zoom: 15,
            streetViewControl: false,
          mapTypeControlOptions: {
        style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
              mapTypeIds:[google.maps.MapTypeId.HYBRID, google.maps.MapTypeId.ROADMAP] 
    },
    center: results[0].geometry.location,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  });
      map.setCenter(results[0].geometry.location);
      marker = new google.maps.Marker({
          map: map,
          position: results[0].geometry.location,
          draggable: true,
          title: 'My Title'
      });
      updateMarkerPosition(results[0].geometry.location);
      updateinput(results[0].geometry.location);
      geocodePosition(results[0].geometry.location);
        
      // Add dragging event listeners.
  google.maps.event.addListener(marker, 'dragstart', function() {
    updateMarkerAddress('Dragging...');
  });
      
  google.maps.event.addListener(marker, 'drag', function() {
    updateMarkerStatus('Dragging...');
    updateMarkerPosition(marker.getPosition());
    updateinput(marker.getPosition());
  });
  
  google.maps.event.addListener(marker, 'dragend', function() {
    updateMarkerStatus('Drag ended');
    geocodePosition(marker.getPosition());
      map.panTo(marker.getPosition()); 
  });
  
  google.maps.event.addListener(map, 'click', function(e) {
    updateMarkerPosition(e.latLng);
    updateinput(e.latLng);
    geocodePosition(marker.getPosition());
    marker.setPosition(e.latLng);
  map.panTo(marker.getPosition()); 
  }); 
  
    } else {
      alert('Geocode was not successful for the following reason: ' + status);
    }
  });
}

function geocodePosition(pos) {
  geocoder.geocode({
    latLng: pos
  }, function(responses) {
    if (responses && responses.length > 0) {
      updateMarkerAddress(responses[0].formatted_address);
      updateaddress(responses[0].address_components);
    } else {
      updateMarkerAddress('Cannot determine address at this location.');
    }
  });
}

function updateMarkerStatus(str) {
  document.getElementById('markerStatus').innerHTML = str;
}

function updateinput(latLng) {
  document.getElementById('lat').value = latLng.lat();
  document.getElementById('lng').value = latLng.lng();
}
function updateaddress(add_components){
    var address_components = add_components;
    var components={}; 
    jQuery.each(address_components, function(k,v1) {jQuery.each(v1.types, function(k2, v2){components[v2]=v1.long_name});})
    for (var key in components) {
        switch(key){
             case "route":
                document.getElementById('street').value = components[key];
                break;
             case "locality":
                document.getElementById('locality').value = components[key];
                break;
             case "country":
                document.getElementById('country').value = components[key];
                break;
             case "postal_code":
                document.getElementById('zipcode').value = components[key];
                break;
             case "administrative_area_level_1":
                document.getElementById('state').value = components[key];
                break;
             case "administrative_area_level_2":
                document.getElementById('district').value = components[key];
                break;
        }
    }
    //document.getElementById('address1').value = components.country;
}
function updateMarkerPosition(latLng) {
  document.getElementById('info').innerHTML = [
    latLng.lat(),
    latLng.lng()
  ].join(', ');
}

function updateMarkerAddress(str) {
  document.getElementById('address').innerHTML = str;
  document.getElementById('address1').value = str;
}
