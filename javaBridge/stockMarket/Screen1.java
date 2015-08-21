package com.example.stockmarket;
// you need the following imports in all Java Bridge apps
import com.google.appinventor.components.runtime.HandlesEventDispatching;
import com.google.appinventor.components.runtime.EventDispatcher;
import com.google.appinventor.components.runtime.Form;
import com.google.appinventor.components.runtime.Component;

// the following components are needed
import com.google.appinventor.components.runtime.Web;
import com.google.appinventor.components.runtime.HorizontalArrangement;
import com.google.appinventor.components.runtime.Label;
import com.google.appinventor.components.runtime.TextBox;
import com.google.appinventor.components.runtime.Button;

// the usual header
public class Screen1 extends Form implements HandlesEventDispatching
{		
	// declare all your components as variables
	private Web web;
	private HorizontalArrangement arrangement1;
	private TextBox symbolTextBox;
	private Label stockLabel;
	private Button getInfoButton;
	
	private String YAHOO_FINANCE_URL="http://download.finance.yahoo.com/d/quotes.csv?f=s0l1&e=.csv&s=";
	
	// don't forget to add permission "android.permission.Internet" in Manifest file
	
	protected void $define()
	{	
		this.Title("Stock Market App");
		arrangement1 = new HorizontalArrangement(this);
		arrangement1.Width(LENGTH_FILL_PARENT);
		symbolTextBox = new TextBox(arrangement1);
		symbolTextBox.Text("GOOG");
		stockLabel = new Label(arrangement1);
		stockLabel.Text("stock info");
		getInfoButton = new Button(this);
		getInfoButton.Text("Get Stock Info");
		web = new Web(this);
		
		EventDispatcher.registerEventForDelegation( this, "Web", "GotText" );
		EventDispatcher.registerEventForDelegation( this, "Button", "Click" );
	}
	public boolean dispatchEvent(Component component, String componentName, String eventName, Object[] params )
	{	
		if( component.equals(web) && eventName.equals("GotText") )
		{
				String result = (String) params[3];
				// we asked for s0 (symbol) and l1 (price) below, so split and take second for price
				String info[] = result.split(",");
				stockLabel.Text("$"+info[1]);
				return true;
		}
		if( component.equals(getInfoButton) && eventName.equals("Click") )
		{
				stockLabel.Text("Accessing web...");
				
				web.Url(YAHOO_FINANCE_URL+symbolTextBox.Text());
				web.Get();
				return true;
		}
		return false;
	}
	
	
}