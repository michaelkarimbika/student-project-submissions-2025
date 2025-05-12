import { Injectable } from '@angular/core';
import { HttpClient,HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {


  private baseur='http://127.0.0.1:8000/api';

  constructor(private http:HttpClient) { }

  //user registration
  registerUser(userData:any):Observable<any>{
    return this.http.post(`${this.baseur}/users/register/`,userData);
  }
  //login
  login(credentials:any):Observable<any>{
    return this.http.post(`${this.baseur}/users/login`,credentials);
  }

  //get recommendations
  getRecommendations(userId:string,token:string):Observable<any>{
   const headers=new HttpHeaders({
    'Authorization':`Token${token}`
   });
   return this.http.get(`${this.baseur}/recomendations/?user_id=${userId}`);
  }
}
