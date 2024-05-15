// var width = 800;
// var page_starter = '<div style="width:' + width + 'px; text-align: center;">';
var page_starter = '<div style="text-align: center;">';

var page1 = page_starter +
        '<img style="width: 600px;" src="instructions/dummy_intro.png"></img>' +
        '</div> <p style="width:800px">In this experiment, you will watch people going to their workplace by car. Their goal is to reach within the remaining time, indicated at the top. To explain the setup, we will just focus on Jane for now, and you will watch different cases of her commute under various time limits, road network configurations, and traffic conditions. To navigate, use the \"Previous\" and \"Next\" buttons or the left and right keys on your keyboard.</p>';
        
var page2 = page_starter +
        '<img src="instructions/aiRight.png" style="width: 100px;' +
            'margin-top: 120px; margin-right: 200px;"></img>' + 
        '<img src="instructions/humanRight.png" style="width: 100px;' +
            'margin-top: 120px; margin-left: 200px;"></img>' + 
        '</div> <p style="width:800px">Jane bought a brand new car that is AI-assisted. In each time step, the car can be driven either by the <b style="color:#ffa000">AI</b> (left picture) or by <b style="color:#762c6c">Jane</b> (right picture). The arrow at the center of the car indicates in which direction the respective driver wants to move.</p>';

var page3 = page_starter +
        '<img style="width: 600px;" src="instructions/dummy_human.gif"></img>' +
        '</div> <p style="width:800px">In this example, <b style="color:#762c6c">Jane starts driving</b> and <b>she has 10 time steps</b> to reach her workplace. Moving 1 tile requires 1 time step. Yay, she managed to reach her workplace on time!</p>';

var page4 = page_starter +
        '<img style="width: 600px;" src="instructions/dummy_ai.gif"></img>' +
        '</div> <p style="width:800px">The AI is driving with the same speed (1 tile per time step). In this example, Jane <b style="color:#ffa000">lets the AI drive</b> and <b>she has 5 time steps</b> to reach her workplace. Unfortunately, she doesn\'t make it on time...</p>';

var page5 = page_starter +
        '<img style="width: 600px;" src="instructions/blocks.gif"></img>' +
        '</div> <p style="width:800px">Each map consists of white tiles that represent roads, and <b>black tiles that are inaccessible</b>. Both Jane and the AI know the map beforehand and, whenever they drive, they tend to take the shortest path that can lead them to the workplace. In this example, Jane takes the lower path because it requires 9 time steps, while the upper path would have required 11 time steps.</p>';

var page6 = page_starter +
        '<img style="width: 600px;" src="instructions/road_closure_human.png"></img>' +
        '</div> <p style="width:800px">The commute is not always so smooth. Sometimes, there are <b style="color:#E6A040">road closures</b> that can make a tile inaccessible. Fortunately, Jane listens to the radio every morning, and she gets informed about potential road closures beforehand.</p>';

var page7 = page_starter +
        '<img style="width: 600px;" src="instructions/road_closure_ai.png"></img>' +
        '</div> <p style="width:800px">However, the AI is not up to date with the latest information on road closures, and it is completely unaware of their existence. Here, the road closure is faded because the current driver (the AI) does not know about it.</p>';

var page8 = page_starter +
        '<img style="width: 600px;" src="instructions/road_closure.gif"></img>' +
        '</div> <p style="width:800px">In this example, the AI starts driving. It takes the lower path, and it discovers there is a road closure. Then, it turns around, and it takes the upper path. The 3x3 rectangle around the car indicates the driver\'s <b style="color:#ffa000">field of vision</b>, and the driver (here, the AI) becomes aware of an unknown obstacle (here, the road closure) only if it enters their field of vision.</p>';

var page9 = page_starter +
        '<img style="width: 600px;" src="instructions/traffic_ai.png"></img>' +
        '</div> <p style="width:800px">However, the AI has its own benefits. In this map, there are tiles that are <b style="color: #EB4D44">usual traffic spots</b>. Each of them can be congested (solid red) or not (red border). <b>The AI has real-time information about their status and Jane knows that</b>. Driving over a congested traffic spot causes an additional <b>delay of 10 time steps.</b></p>';

var page10 = page_starter +
        '<img style="width: 600px;" src="instructions/traffic_ai.gif"></img>' +
        '</div> <p style="width:800px">In this example, the AI knows about the status of the usual traffic spots. Although the upper path is slightly longer, the traffic spot in it is not congested, while the traffic spot in the lower path is congested. Therefore, the AI decides to take the upper path.</b></p>';

var page11 = page_starter +
        '<img style="width: 600px;" src="instructions/traffic_human.png"></img>' +
        '</div> <p style="width:800px">Let\'s look at the same map, but now with Jane being the driver. Jane is familiar with the locations of the usual traffic spots, but she is not aware of their current status (hence, they appear faded on the map). <b>As far as she knows, each one of them has a fifty-fifty chance of being congested.</b></p>';

var page12 = page_starter +
        '<img style="width: 600px;" src="instructions/traffic_human.gif"></img>' +
        '</div> <p style="width:800px">In this example, Jane believes each path has a fifty-fifty chance of being congested. Since the lower path is shorter, she decides to take it. After she observes there is congestion on her path, she figures that it is still better for her to stay in the traffic for 10 time steps and keep going, rather than turning around and taking the upper path. <b>As far as she knows, the upper path could also be congested</b>, since the second traffic spot never enters her field of vision.</p>';
        
var page13 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_human_example/frame_0.png"></img>' +
        '</div> <p style="width:800px">Let\'s go through the following example to understand how all the building blocks work together. Here, <b style="color:#762c6c">Jane starts driving</b>, and she is aware there is a <b style="color:#E6A040">road closure</b>. Moreover, she knows the locations of the two <b style="color: #EB4D44">usual traffic spots</b>, but she does not know whether they are congested or not. She has <b>40 time steps to reach her workplace.</b></p>';

var page14 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_human_example/frame_3.png"></img>' +
        '</div> <p style="width:800px">So far, Jane\'s commute has taken 3 time steps (3 tiles x 1 time step each). Since she knows about the road closure, Jane has decided to take a turn instead of going straight.</p>';

var page15 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_human_example/frame_4.png"></img>' +
        '</div> <p style="width:800px">At this point, she decides to go right. As far as she knows, each traffic spot has a fifty-fifty chance of being congested and the upper path is longer.</p>';

var page16 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_human_example/frame_10.png"></img>' +
        '</div> <p style="width:800px">Jane observes the congested traffic spot. Nevertheless, she decides to keep going right.</p>';

var page17 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_human_example/frame_11.png"></img>' +
        '</div> <p style="width:800px">She is stuck in traffic. She has 29 time steps remaining to reach her workplace.</p>';

var page18 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_human_example/frame_22.png"></img>' +
        '</div> <p style="width:800px">She exits the congested traffic spot. She has 18 time steps remaining. The transition from the traffic spot to her current tile took 11 time steps (1 as usual + 10 because of the traffic).</p>';

var page19 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_human_example/frame_24.png"></img>' +
        '</div> <p style="width:800px">Yay, she managed to reach her workplace on time!</p>';

var page20 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_ai_example/frame_0.png"></img>' +
        '</div> <p style="width:800px">Now, let\'s go through an example in the same map, but with the <b style="color:#ffa000">AI driving the car</b>. Recall that the AI knows the current status of the two usual traffic spots, but it is not aware of the road closure.</p>';

var page21 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_ai_example/frame_3.png"></img>' +
        '</div> <p style="width:800px">So far, the commute has taken 3 time steps (3 tiles x 1 time step each). The AI has decided to take the lower path, since it is not aware of the road closure and it is trying to avoid the congested traffic spot.</p>';

var page22 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_ai_example/frame_7.png"></img>' +
        '</div> <p style="width:800px">The AI observes the road closure, and it decides to turn around.</p>';

var page23 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_ai_example/frame_14.png"></img>' +
        '</div> <p style="width:800px">At this point, the AI decides to go up. Although the upper path is longer, it is faster because the traffic spot at the top is not congested.</p>';

var page24 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_ai_example/frame_18.png"></img>' +
        '</div> <p style="width:800px"><b style="color:#B56F48">Oh no, an accident!</b> Accidents can randomly appear on any white tile, and they make it inaccessible. <b>Neither Jane nor the AI know about an accident, until it enters their field of vision.</b></p>';

var page25 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_ai_example/frame_20.png"></img>' +
        '</div> <p style="width:800px">Here, even though it is slightly longer, the AI has to take the left path due to the right path being blocked by the accident.</p>';

var page26 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_ai_example/frame_24.png"></img>' +
        '</div> <p style="width:800px">The traffic spot is not congested, therefore, it takes only 1 time step for the AI to drive over that tile.</p>';

var page27 = page_starter +
        '<img style="width: 500px;" src="instructions/world05_ai_example/frame_28.png"></img>' +
        '</div> <p style="width:800px">Phew, what a ride... Jane reached her workplace on time!</p>';

var page28 = page_starter +
        '</div> <p style="width:800px">At this point, you should be familiar with the basic elements of the driving environment used in this experiment. If you need to review some of the explanations, you can click \"Previous\" (or the left key on your keyboard) and navigate through the instructions. <b>Click \"Next\" only when you are ready to proceed.</b></p>';

var instruction_driving_pages = [
        page1,
        page2,
        page3,
        page4,
        page5,
        page6,
        page7,
        page8,
        page9,
        page10,
        page11,
        page12,
        page13,
        page14,
        page15,
        page16,
        page17,
        page18,
        page19,
        page20,
        page21,
        page22,
        page23,
        page24,
        page25,
        page26,
        page27,
        page28
]


var instruction_driving_images = [
        'instructions/dummy_intro.png',
        'instructions/dummy_ai.gif',
        'instructions/dummy_human.gif',
        'instructions/blocks.gif',
        'instructions/road_closure_human.png',
        'instructions/road_closure_ai.png',
        'instructions/road_closure.gif',
        'instructions/traffic_ai.png',
        'instructions/traffic_ai.gif',
        'instructions/traffic_human.png',
        'instructions/traffic_human.gif',
        'instructions/world05_human_example/frame_0.png',
        'instructions/world05_human_example/frame_3.png',
        'instructions/world05_human_example/frame_4.png',
        'instructions/world05_human_example/frame_10.png',
        'instructions/world05_human_example/frame_11.png',
        'instructions/world05_human_example/frame_22.png',
        'instructions/world05_human_example/frame_24.png',
        'instructions/world05_ai_example/frame_0.png',
        'instructions/world05_ai_example/frame_3.png',
        'instructions/world05_ai_example/frame_7.png',
        'instructions/world05_ai_example/frame_14.png',
        'instructions/world05_ai_example/frame_18.png',
        'instructions/world05_ai_example/frame_20.png',
        'instructions/world05_ai_example/frame_24.png',
        'instructions/world05_ai_example/frame_28.png',
        'instructions/qs_2.png',
        'instructions/qs_3.png'
];