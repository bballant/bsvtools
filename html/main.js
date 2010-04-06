var tl; // global timeline var
var markers = [];
var map;

// Helper Functions //

var resizeTimerID = null;
function onResize() {
    if (resizeTimerID == null) {
        resizeTimerID = window.setTimeout(function() {
            resizeTimerID = null;
            tl.layout();
        }, 500);
    }
}

var util = {
    formatForWeb: function(timestamp) {
        return timestamp.getFullYear() + "-" +
            (timestamp.getMonth() + 1) + "-" + timestamp.getDate() +
            "T" + timestamp.getHours() + ":" + timestamp.getMinutes() +
            ":" + timestamp.getSeconds();
    }
}


// onclick handler //
function addEventHandler(viewer) {
    Timeline.OriginalEventPainter.prototype._showBubble = function(x, y, evt) {
        var lat = evt._obj.point.lat;
        var lon = evt._obj.point.lon;
        var start = evt.getStart();
        var startstr = start ? start.toString() : "";
        // remove existing markers
        while(markers.length != 0)
            map.removeOverlay(markers.pop());
    
        if (lat && lon) {
            marker = new GMarker(new GLatLng(lat, lon));
            markers.push(marker);
            map.addOverlay(marker);
            marker.openInfoWindowHtml(startstr + "<br/>" + lat + ", " + lon);
        }
        
        if (start) {
            viewer.loadData({'starttime': util.formatForWeb(start)});
        } 
    }
}
  
// Create functions called from Ajax callback w/ json 'data' //

// maps a polyline for points in data //
function createMap(data) {
    if (data.length<1 || !GBrowserIsCompatible()) 
        return; 

    map = new GMap2(
        document.getElementById("map_canvas"));
    map.addControl(new GSmallMapControl());
    map.addControl(new GMapTypeControl());
    map.setCenter(
        new GLatLng(data.events[0].point.lat, data.events[0].point.lon), 13); 

    point_list = [];
    data.events.each(function(item) {
    point_list.push(
        new GLatLng(item.point.lat, item.point.lon));        
    });

    var polyline = new GPolyline(point_list, "#ff0000", 2);
    /*
    GEvent.addListener(polyline, 'click', function(latlng) {
      alert(latlng.lat() + " " + latlng.lng());
    });
    */
    map.addOverlay(polyline);
}

// creates a timeline of points in data on timline canvas //
function createTimeline(data, canvas) {
    var keyword = "tagged";   // highlight keyword 
    
    var theme 		= Timeline.ClassicTheme.create();
    theme.event.bubble.width 	= 350;
    theme.event.bubble.height 	= 300;
    theme.highlightColor 		= "#FFFF66";
    
    // create eventSource and load data
    var eventSource = new Timeline.DefaultEventSource();
    eventSource.loadJSON(data, document.location.href);
    
    // set startdate
    var da = data.timestamp.split(/[\-\.\:T]/);
    var startdate = new Date(da[0],da[1]-1,da[2],da[3],da[4],da[5]);    
    //var startdate = new Date("Mar 02 2010 19:33:10 GMT-0500"); // initial date
    var bandInfos = [
        Timeline.createBandInfo({
           width: "60%", 
           intervalUnit: Timeline.DateTime.MINUTE, 
           intervalPixels: 300,
           theme: theme,
           eventSource: eventSource,
           date: startdate 
         }),
        Timeline.createBandInfo({
          showEventText: false,
          width: "40%", 
          intervalUnit: Timeline.DateTime.HOUR, 
          intervalPixels: 500,
          eventSource: eventSource,
          theme: theme,
          overview: true,
          date: startdate 
         })     
    ];
    bandInfos[0].highlight = true;
    bandInfos[1].syncWith = 0;
    bandInfos[1].highlight = true;
    // create the timeline
    tl = Timeline.create(canvas, bandInfos);
    // add the highlighting for events
    var highlightMatcher = function(evt) {
        var description = evt.getDescription();
        var regex = new RegExp(keyword, "i");
        if (regex.test(description)) {
            return true;
        } return -1;
    };
    for (var i=0; i<bandInfos.length; i++)
        tl.getBand(i).
            getEventPainter().
            setHighlightMatcher(highlightMatcher);
    
    // Paint the mofo
    tl.paint();
}


// FrameViewer object handles all interaction with the Frame Image Viewer //
// Constructor takes in the div and button elements used to draw viewer //
function FrameViewer(
		canvas, 
		btn_prev_frame, 
		btn_prev_second, 
		btn_next_frame, 
		btn_next_second) {
    
	// Private instance variables //
    var IMG_WIDTH 		= 192;
    var IMG_HEIGHT 		= 144;
    var ROWS_TO_SHOW 	= 3;
    var curr_row 		= 0;
    var data 			= null;
    
    
    // Private methods //
    
    // Caches image objects and stores directly in data //
    function load_images() {
        data.each(function(frame) {
            var imgs = []
            frame.images.each(function(imgstr) {
                var img = new Image(IMG_WIDTH, IMG_HEIGHT);
                img.src = "/img/" + imgstr;
                img.style.float = "left";
                imgs.push(img);        
            });
            frame['imageobjs'] = imgs;
        })      
    }
  
    // use DOM to draw the viewer HTML on canvas //
    function draw_viewer() {
        canvas.innerHTML = "";
        var n = curr_row;
        while(n < data.length && 
                n < (curr_row + ROWS_TO_SHOW)) {
            var div = document.createElement("div");
            div.style.width = 8 * IMG_WIDTH + "px";
            var h3 = document.createElement("span");
            h3.innerHTML = data[n].timestamp.replace('T', ' ');
            div.appendChild(h3);
            div.appendChild(document.createElement("br"));
            data[n].imageobjs.each(function(imageobj) {
                imageobj.addEventListener("click", function() {
                    window.open(imageobj.src);
                }, false);
                div.appendChild(imageobj);
            });
            canvas.appendChild(div); 
            n++;
        }      
    }
    
    // Called from ajax callback //
    function update(d) {
        data = d;
        load_images();
        draw_viewer();
    }
    
    
    // Privileged method (public) //
    // Makes ajax request to get data based on params //
    this.loadData = function(params) {
        var url = "/images";
        var pstrs = [];
        if (params.starttime && params.starttime.length != 0) {
        pstrs.push("starttime=" + params.starttime);
        if (params.endtime && params.endtime.length != 0) 
            pstrs.push("endtime=" + params.endtime);
        if (params.duration && params.duration.length !=0)
            pstrs.push("duration=" + params.duration);
        if (params.jump && params.jump.length != 0)
            pstrs.push("jump=" + params.jump);
        }
        if (params.count && params.count.length !=0)
            pstrs.push("count=" + params.count);

        url += "?" + pstrs.join("&");

        //reset 
        canvas.innerHTML = "Loading...";

        new Ajax.Request(url, {
            method: 'get',
            onSuccess: function(transport, json) {
                var response = transport.responseText || "[]";
                var data = eval("(" + response + ")");
                update(data);
            }
        });
    }
    
    
    // Set Up Button Listeners //
    
    var parent = this;
    btn_prev_frame.addEventListener("click", 
        function() {
            if (curr_row == 0) { 
                return;
            }
            curr_row -= 1;
            draw_viewer();
        }, false);
     
    btn_prev_second.addEventListener("click", 
        function() {
            ts = data[curr_row].timestamp;
            curr_row = 0;
            parent.loadData({'starttime': ts, 'jump': -1});
        }, false);

    btn_next_frame.addEventListener("click", 
        function() {
            if (curr_row >= data.length - ROWS_TO_SHOW) {
                ts = data[curr_row+1].timestamp;
                curr_row = 0;
                parent.loadData( {'starttime': ts});
                return;
            }
            curr_row += 1;
            draw_viewer();
        }, false);

    btn_next_second.addEventListener("click", 
        function() {
            ts = data[curr_row].timestamp;
            curr_row = 0;
            parent.loadData( {'starttime': ts, 'jump': 1});
        }, false);    
}