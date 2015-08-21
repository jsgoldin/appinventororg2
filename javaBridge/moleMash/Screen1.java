// A simple MoleMash game with a timer
package com.example.molemash;
// you need the following imports in all Java Bridge apps
import com.google.appinventor.components.runtime.HandlesEventDispatching;
import com.google.appinventor.components.runtime.EventDispatcher;
import com.google.appinventor.components.runtime.Form;
import com.google.appinventor.components.runtime.Component;

// the components for the MoleMash game
import com.google.appinventor.components.runtime.Button;
import com.google.appinventor.components.runtime.Canvas;
import com.google.appinventor.components.runtime.Clock;
import com.google.appinventor.components.runtime.Label;
import com.google.appinventor.components.runtime.ImageSprite;
import com.google.appinventor.components.runtime.HorizontalArrangement;
// import Java's Random module
import java.util.Random;

// the usual header for a Java Bridge app
public class Screen1 extends Form implements HandlesEventDispatching
{		
	// declare all your components as variables
	private Canvas canvas1;
	private Label headerLabel;
	private Clock moleClock;
	private Clock gameClock;
	private HorizontalArrangement horizArrangement;
	private Label timeLeftLabel;
	private Label timeLeftValueLabel;
	private Label spaceLabel;
	private Label scoreLabel;
	private Label scoreValueLabel;
	private ImageSprite moleSprite;
	
	protected void $define()
	{
		// create your components and set their initial properties
		headerLabel = new Label (this);
		headerLabel.Text("MOLEMASH-- touch the mole to earn points!");
		canvas1 = new Canvas(this);
		canvas1.BackgroundColor(COLOR_GRAY);
		canvas1.Width(LENGTH_FILL_PARENT); 
		canvas1.Height(300);
		
		moleSprite = new ImageSprite(canvas1);
		// be sure and place a file mole.png in the assets folder of your project!
		moleSprite.Picture("mole.png");
		
		moleClock = new Clock(this);
		gameClock = new Clock(this);
		horizArrangement = new HorizontalArrangement(this);
		timeLeftLabel= new Label(horizArrangement);
		timeLeftLabel.Text("Time Left:");
		timeLeftValueLabel= new Label(horizArrangement);
		timeLeftValueLabel.Text("60");
		spaceLabel = new Label(horizArrangement);
		spaceLabel.Text("   ");
		scoreLabel= new Label(horizArrangement);
		scoreLabel.Text("Score:");
		scoreValueLabel= new Label(horizArrangement);
		scoreValueLabel.Text("0");
		EventDispatcher.registerEventForDelegation( this, "Canvas/Sprite", "Touched" );
		EventDispatcher.registerEventForDelegation( this, "ClockMoleTimer", "Timer" );
	}
	public boolean dispatchEvent(Component component, String componentName, String eventName, Object[] params )
	{
		// when mole is touched, add a point. Need to covert text to int and back
		if( component.equals(moleSprite) && eventName.equals("Touched") )
		{
				int score = Integer.parseInt(scoreValueLabel.Text());
				score = score+1;
				scoreValueLabel.Text(String.valueOf(score));
				return true;
		}
		// count down the clock on the clock timer
		if( component.equals(gameClock) && eventName.equals("Timer") )
		{
				int count = Integer.parseInt(timeLeftValueLabel.Text());
				count = count - 1;
				timeLeftValueLabel.Text(String.valueOf(count));
				if (count==0) {
					//game is over
					gameClock.TimerEnabled(false);
					moleClock.TimerEnabled(false);
					timeLeftValueLabel.Text("Game Over");
					
				}					
				return true;
		}
		// on mole timer, move the mole randomly
		if( component.equals(moleClock) && eventName.equals("Timer") )
		{
				Random random = new Random();
				int x= random.nextInt(canvas1.Width()-moleSprite.Width());
				int y= random.nextInt(canvas1.Height()-moleSprite.Height());
				moleSprite.MoveTo(x, y);
				
				return true;
		}
		return false;
	}
	
}