package com.example.clickred;
// you need the following imports in all Java Bridge apps
import com.google.appinventor.components.runtime.HandlesEventDispatching;
import com.google.appinventor.components.runtime.EventDispatcher;
import com.google.appinventor.components.runtime.Form;
import com.google.appinventor.components.runtime.Component;

// import any components you are going to use in your app. In this case, just Button
import com.google.appinventor.components.runtime.Button;

// you can use the following header for all apps
public class Screen1 extends Form implements HandlesEventDispatching
{		
	// declare all your components as instance variables
	private Button redButton;
	
	// $define is where you'll create components, initialize properties and make any calls that 
	// you'd put in Screen.Initialize of an App Inventor app
	protected void $define()
	{	
		// create the button component
		redButton = new Button(this);  // the parameter defines the parent for the component, 
									   // in this case, "this" the screen.
									   // if you had an arrangement, you'd refer to it instead.
		redButton.Text( "Turn RED" );
		redButton.BackgroundColor(COLOR_GREEN ); 
		
		// register all events that you want to respond to. The second parameter is
	    // just a name, the third is the event you care about and its component-independent
	    // so you, e.g., you need just one "Click" event even if many buttons
		EventDispatcher.registerEventForDelegation( this, "RedButtonClick", "Click" );
	}
	// dispatchEvent handles all events. You'll use an if-else to identify the component and
	// event and you can either call a method or just respond to the event directly 
	// params provides the event parameters (not used here)
	public boolean dispatchEvent(Component component, String componentName, String eventName, Object[] params )
	{	
		if( component.equals(redButton) && eventName.equals("Click") )
		{
				RedButtonClick();
				return true;
		}
		// here is where you'd check for other events of your app...
		return false;
	}
	// this is the event handler that dispatchEvent above calls. We just set the button background
	public void RedButtonClick()
	{
		redButton.BackgroundColor(COLOR_RED);	
	}
	
}