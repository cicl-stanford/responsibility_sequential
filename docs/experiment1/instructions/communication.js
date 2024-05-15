var page_starter = '<div style="text-align: center;">';

var page1 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/ai_no_intro.png"></img>' +
        '</div> <p style="width:800px">Before we proceed to the main experiment, let\'s take a look at one last feature of the AI-assisted car. To give Jane more flexibility, the AI is programmed to <b>communicate</b> with her based on the following protocol.</p>';

var page2 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/ai_no_q.png"></img>' +
        '</div> <p style="width:800px">On a <b>single intersection chosen at random</b>, the AI asks Jane to confirm whether she wants it to keep driving. Jane observes the direction that the AI wants to take, and she either confirms or takes control of the car. In the example above, the AI lets Jane know it plans to go right, and Jane confirms.</p>';

var page3 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/ai_no_end.png"></img>' +
        '</div> <p style="width:800px">After their short interaction, the AI drives the rest of the way to the workplace. Yay, Jane reached the workplace on time!</p>';

var page4 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/ai_no.gif"></img>' +
        '</div> <p style="width:800px">Take some time to watch the example again and familiarize yourself with the communication process.</p>';

var page5 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/ai_yes_intro.png"></img>' +
        '</div> <p style="width:800px">Now, let\'s watch another example.</p>';

var page6 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/ai_yes_q.png"></img>' +
        '</div> <p style="width:800px">After a few time steps, the AI lets Jane know it plans to go right and it asks her to confirm. She decides to drive the rest of the way herself. Notice that there are 16 time steps remaining.</p>';

var page7 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/ai_yes_change.png"></img>' +
        '</div> <p style="width:800px">Now, there are 15 time steps remaining, the car has not moved and Jane is in control. Switching drivers takes one time step. <b>Jane\'s choice is final; she cannot give control back to the AI.</b></p>';

var page8 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/ai_yes_end.png"></img>' +
        '</div> <p style="width:800px">After their short interaction, Jane drives the rest of the way to the workplace. Yay, she reached the workplace on time!</p>';

var page9 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/ai_yes.gif"></img>' +
        '</div> <p style="width:800px">Take some time to watch the example again and familiarize yourself with the communication and control switching process.</p>';

var page10 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/human_no.gif"></img>' +
        '</div> <p style="width:800px">If Jane is the one driving the car at the start, the communication works similarly. At a <b>single intersection chosen at random</b>, the AI asks Jane if she wants it to take control of the car. Here, Jane refuses.</p>';

var page11 = page_starter +
        '<img style="width: 600px;" src="instructions/comm/human_yes.gif"></img>' +
        '</div> <p style="width:800px">In this new example, the AI asks Jane if she wants it to take control of the car, and Jane agrees to let it drive. <b>Her choice is final; she cannot take back control and the AI drives the rest of the way.</b></p>';

var page12 = page_starter +
        '</div> <p style="width:800px">In this experiment, you will watch different cases of people\'s commute, all using the same AI-assisted car. Unfortunately, no one manages to reach their workplace on time. In each case, you will be asked to judge how <b>responsible</b> the person and the AI are for failing to arrive on time. Now, you will watch another example, which will be exactly like the cases you will watch during the main experiment.</p>';

var instruction_communication_pages = [
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
        page12
]


var instruction_communication_images = [
        'instructions/comm/ai_no_intro.png',
        'instructions/comm/ai_no_q.png',
        'instructions/comm/ai_no_end.png',
        'instructions/comm/ai_no.gif',
        'instructions/comm/ai_yes_intro.png',
        'instructions/comm/ai_yes_q.png',
        'instructions/comm/ai_yes_change.png',
        'instructions/comm/ai_yes_end.png',
        'instructions/comm/ai_yes.gif',
        'instructions/comm/human_no.gif',
        'instructions/comm/human_no_q.png',
        'instructions/comm/human_no_intro.png',
        'instructions/comm/human_no_end.png',
        'instructions/comm/human_yes.gif'
];
