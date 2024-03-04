/* This is your dashboard JavaScript, it has been embedded into dashboard.html */

function hide_dashboard()
{
    videofeed.innerHTML = ' ';
    load_robot_button.style.display = "block";
    robot_buttons.style.display = "none";
    shutdown_robot_button.style.display = "none"
}
function show_dashboard()
{
    loader.style.display = 'none';
    videofeed.innerHTML = '<img src="/videofeed" class="videofeed"></img>';
    robot_buttons.style.display = "block";
    shutdown_robot_button.style.display = "block";
    load_robot_button.style.display = "none";
}

load_robot_button.onclick = load_robot;
function load_robot()
{
    if (robot_loaded == 0)
    {
        load_robot_button.style.display = 'none';
        loader.style.display = 'block';
        new_ajax_helper('/load_robot', defaulthandler=load_robot_handler);
    }
}
function load_robot_handler(response) { show_dashboard(); robot_loaded = 1; }

shutdown_robot_button.onclick = shutdown_robot;
function shutdown_robot()
{
    if (robot_loaded == 1)
    {
        hide_dashboard();
        new_ajax_helper('/shutdown_robot', defaulthandler=shutdown_robot_handler);
    }
}
function shutdown_robot_handler(response)
{
    load_robot_button.style.display = "block"; robot_loaded = 0;
}

//hide or show dashboard based on initial value from server on page load
if (robot_loaded == 1) {
    show_dashboard();
} else {
    hide_dashboard();
}

turn_on_detection_button.onclick = turn_on_detection;
function turn_on_detection()
{
    if (robot_loaded == 1)
    {
        new_ajax_helper('/turn_on_detection');
    }
}


turn_off_detection_button.onclick = turn_off_detection;
function turn_off_detection()
{
    if (robot_loaded == 1)
    {
        new_ajax_helper('/turn_off_detection');
    }
}


look_down_button.onclick = look_down;
function look_down()
{
    if (robot_loaded == 1)
    {
        new_ajax_helper('/look_down');
    }
}


look_up_button.onclick = look_up;
function look_up()
{
    if (robot_loaded == 1)
    {
        new_ajax_helper('/look_up');
    }
}

move_forward_button.onclick = move_forward
function move_forward()
{
    if (robot_loaded == 1)
    {
        new_ajax_helper('/move_forward/90');
	console.log("ran")
    }
}


move_backward_button.onclick = move_backward
function move_backward()
{
    if (robot_loaded == 1)
    {
        new_ajax_helper('/move_forward/270');
	console.log("ran")
    }
}

stop_button.onclick = stop;
function stop()
{
    if (robot_loaded == 1)
    {
        new_ajax_helper('/stop');
    }
}

start_mission_button.onclick = start_mission;
function start_mission()
{
    if (robot_loaded == 1)
    {
	let formobject = new FormData();
	formobject.append("red_num", red_num.value);
	formobject.append("green_num", green_num.value);
	formobject.append("blue_num", blue_num.value);
        new_ajax_helper('/start_mission',defaulthandler,formobject);
	robot_buttons.style.display = "none";
    }
}



stop_mission_button.onclick = stop_mission;
function stop_mission()
{
    if (robot_loaded == 1)
    {
	robot_buttons.style.display = "block";
        new_ajax_helper('/stop_mission');
    }
}
