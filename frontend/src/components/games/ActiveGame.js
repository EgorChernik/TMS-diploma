import React, {Component} from 'react'
import { createGame } from '../../store/actions/gamesActions'
import { connect } from 'react-redux'
import { Redirect } from "react-router-dom";
import { spinner, changeColor, collectFleet } from '../../utils';


class ActiveGame extends Component {

    
    
    // handleChange = (e) => {
    //     this.setState({
    //         [e.target.id]: e.target.value
    //     })
    // }
    // handleColor = (e) => {
    //     changeColor(e.target.id)
    // }
    // handleSubmit = (e) => {
    //     e.preventDefault();        
    //     const fleet = collectFleet(this.state.size);
    //     this.setState({ isLoading: true });
    //     console.log(this.state);
    //     this.props.createGame(this.state, fleet)
    //         .then((render) => {render(<Redirect to="/active-game/" />)})
    //         .finally(() => this.setState({isLoading: false})); 
    // }

    render() {
        // if (this.state.isLoading) {
        //     return spinner()
        // }
        // if (!this.props.auth.authToken) {

        //     return <Redirect to="/login"/>;
        // }
         
        return (
            <div className="container">
                <form onSubmit={this.handleSubmit} onChange={this.handleChange} className="white">
                    <h5 className="grey-text text-darken-3">New Game</h5>
                    <div>
                        <table id='battlemap' onClick={this.handleColor} className='tableMap'>
                            <tbody>
                                {/* {table(this.state.size)} */}
                            </tbody>
                        </table>
                    </div>

                    <div className="input-field">
                        <button className="btn pink lighten-1 z-depth-0">Create</button>
                    </div>
                </form>
            </div>
        )
    }
}

const mapStateToProps = (state) => {
    return {
        auth: state.auth,
        username: state.username,
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
        createGame: (data, fleet) => dispatch(createGame(data,fleet))
    }
}

export default connect(mapStateToProps, mapDispatchToProps)(ActiveGame)